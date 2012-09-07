# -*- coding: utf-8 -*-

import sys
import urllib,urllib2
import sparql

class OpenDataPortal:

    def __init__(self):
       self.manifestnum = 0
       self.manifestf = open('manifest.xml','w')
       self.manifestf.write("""<?xml version="1.0" encoding="UTF-8"?>
<ecodp:manifest
	xmlns:ecodp="http://ec.europa.eu/open-data/ontologies/ec-odp#"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xsi:schemaLocation="http://ec.europa.eu/open-data/ontologies/protocol-v1.0/ odp-protocol.xsd"
	ecodp:version="1.0"
	ecodp:package-id="EEA"
	ecodp:creation-date-time="2012-04-26T11:22:35"
	ecodp:publisher="http://publications.europa.eu/resource/authority/corporate-body/EEA"
	ecodp:priority="normal">
""")
    def createManifestLine(self, dataseturi, identifier):
        self.manifestnum += 1
        self.manifestf.write("""<ecodp:action ecodp:id="add%d" ecodp:object-uri="%s" ecodp:object-type="dataset">
		<ecodp:add-replace ecodp:object-status="published"  ecodp:package-path="/datasets/%s.rdf"/>
	</ecodp:action>\n""" % ( self.manifestnum, dataseturi, identifier))

    def enditall(self):
        self.manifestf.write("""</ecodp:manifest>\n""")
        self.manifestf.close()

# http://www.eea.europa.eu/data-and-maps/data/urban-atlas
# For examples of datafilelink see http://www.eea.europa.eu/data-and-maps/data/urban-atlas/germany/@@rdf
# For examples of sparql queries see http://www.eea.europa.eu/data-and-maps/data/biogeographical-regions-europe/codelist-for-bio-geographical-regions/@@rdf

    def createRecord(self, dataseturi, identifier):
        query = { 'query':"""
PREFIX a: <http://www.eea.europa.eu/portal_types/Data#>
PREFIX dt: <http://www.eea.europa.eu/portal_types/DataTable#>
PREFIX org: <http://www.eea.europa.eu/portal_types/Organisation#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX ecodp: <http://ec.europa.eu/open-data/ontologies/ec-odp#>
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX datafilelink: <http://www.eea.europa.eu/portal_types/DataFileLink#>
PREFIX datafile: <http://www.eea.europa.eu/portal_types/DataFile#>

CONSTRUCT {
 ?dataset a dcat:Dataset;
       dct:publisher <http://publications.europa.eu/resource/authority/corporate-body/EEA>;
       ecodp:datasetStatus <http://ec.europa.eu/open-data/kos/dataset-status/Completed>;
       ecodp:contactPoint <http://www.eea.europa.eu/data-and-maps/data-providers-and-partners/european-environment-agency>;
       dct:license <http://creativecommons.org/licenses/by/2.5/dk/>;
       dct:title ?title;
       dct:description ?description;
       dct:identifier `STR(?id)`;
       dct:issued ?effective;
       dct:modified ?modified;
       ecodp:keyword ?theme;
       dct:spatial ?pubspatial.
 ?dataset dcat:distribution ?datafile .
 ?datafile dcat:accessURL ?downloadUrl.
 ?datafile a <http://www.w3.org/TR/vocab-dcat#Download>;
       ecodp:distributionFormat ?format;
       dct:description ?dftitle;
       dct:modified ?dfmodified
}
WHERE {
  {
   ?dataset a a:Data ;
        a:id ?id;
        dct:title ?title;
        dct:description ?description;
        dct:hasPart ?datatable.
   OPTIONAL { ?dataset dct:issued ?effective }
   OPTIONAL { ?dataset dct:modified ?modified }
   ?datatable dct:hasPart ?datafile.
   { 
     {
       SELECT DISTINCT ?datafile STRDT(bif:concat(?datafile,'/at_download/file'), xsd:anyURI) AS ?downloadUrl ?format
       WHERE {
         ?datafile a datafile:DataFile;
                   dct:format ?format
       }
     }
   } UNION {
     {
       SELECT DISTINCT ?datafile STRDT(?remoteUrl, xsd:anyURI) AS ?downloadUrl 'application/octet-stream' AS ?format
       WHERE {
         ?datafile a datafilelink:DataFileLink;
                   datafilelink:remoteUrl ?remoteUrl
       }
     }
   }
   ?datafile dct:title    ?dftitle .
   ?datafile dct:modified ?dfmodified
  } UNION {
   ?dataset dct:subject ?theme  FILTER (isLiteral(?theme) && !REGEX(?theme,'[()/]'))
  } UNION {
   ?dataset dct:spatial ?spatial .
   ?spatial owl:sameAs ?pubspatial
        FILTER(REGEX(?pubspatial, '^http://publications.europa.eu/resource/authority/country/'))
  }
  FILTER (?dataset = <%s> )
}
""" % dataseturi,
'format':'application/xml' }

        url = "http://semantic.eea.europa.eu/sparql?" + urllib.urlencode(query)

        outf = open('datasets/' + identifier + '.rdf', "w")
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        urllib2.install_opener(opener)
        req = urllib2.Request(url)
        req.add_header("Accept", "application/xml")
        conn = urllib2.urlopen(req)

        if not conn:
            raise IOError, "Failure in open"

        data = conn.read(8192)
        while data:
            outf.write(data)
            data = conn.read(8192)
        conn.close()
        outf.close()

#------------------------
#FILTER(?dataset = <http://www.eea.europa.eu/data-and-maps/data/corine-land-cover-2000-clc2000-seamless-vector-database-2>)
listq = """
PREFIX a: <http://www.eea.europa.eu/portal_types/Data#>
PREFIX dct: <http://purl.org/dc/terms/>
SELECT DISTINCT ?dataset ?id
WHERE {
  ?dataset a a:Data ;
        a:id ?id;
        dct:description ?description;
        dct:hasPart ?datatable.
  OPTIONAL {?dataset dct:isReplacedBy ?isreplaced }
  ?datatable dct:hasPart ?datafile.
  FILTER(!BOUND(?isreplaced))
}
"""
# ?datafile dct:issued ?effective.
result = sparql.query("http://semantic.eea.europa.eu/sparql", listq)
odp = OpenDataPortal()
for row in result.fetchall():
    print "\t".join(map(str,row))
    odp.createRecord(str(row[0]),str(row[1]))
    odp.createManifestLine(str(row[0]),str(row[1]))
odp.enditall()
# Create zip file here
