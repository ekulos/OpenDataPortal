# -*- coding: utf-8 -*-

import sys
import urllib,urllib2
import sparql

class OpenDataPortal:

    def __init__(self):
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
        self.manifestf.write("""<ecodp:action ecodp:id="add1" ecodp:object-uri="%s" ecodp:object-type="dataset">
		<ecodp:add-replace ecodp:object-status="published"  ecodp:package-path="/datasets/%s.rdf"/>
	</ecodp:action>""" % ( dataseturi, identifier))

    def enditall(self):
        self.manifestf.write("""</ecodp:manifest>\n""")
        self.manifestf.close()

    def createRecord(self, dataseturi, identifier):
        query = { 'query':"""
PREFIX a: <http://www.eea.europa.eu/portal_types/Data#>
PREFIX dt: <http://www.eea.europa.eu/portal_types/DataTable#>
PREFIX org: <http://www.eea.europa.eu/portal_types/Organisation#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX ecodp: <http://ec.europa.eu/open-data/ontologies/ec-odp#>
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

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
 ?datafile dcat:accessURL `IRI(bif:concat(?datafile,'/at_download/file'))`;
       a <http://www.w3.org/TR/vocab-dcat#Download>;
       ecodp:distributionFormat "text/html";
       dct:description ?dftitle;
       dct:modified ?dfmodified
}
WHERE {
  ?dataset a a:Data ;
        a:id ?id;
        dct:title ?title;
        dct:hasPart ?datatable.
  ?datatable dct:hasPart ?datafile.
  ?datafile dct:title ?dftitle;
            dct:modified ?dfmodified
  FILTER (?dataset = <%s> )
  OPTIONAL { ?dataset dct:description ?description }
  OPTIONAL { ?dataset dct:effective ?effective }
  OPTIONAL { ?dataset dct:modified ?modified }
  OPTIONAL { ?dataset a:themes ?theme }
  OPTIONAL { ?dataset dct:spatial ?spatial .
   ?spatial owl:sameAs ?pubspatial
  FILTER(REGEX(?pubspatial, '^http://publications\\\.europa\\\.eu/resource/authority/country/'))
   }
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
listq = """
PREFIX a: <http://www.eea.europa.eu/portal_types/Data#>
SELECT DISTINCT ?dataset ?id
WHERE {
  ?dataset a a:Data ;
        a:id ?id
FILTER(?dataset = <http://www.eea.europa.eu/data-and-maps/data/corine-land-cover-2000-clc2000-seamless-vector-database-2>)
}
"""
result = sparql.query("http://semantic.eea.europa.eu/sparql", listq)
odp = OpenDataPortal()
for row in result.fetchall():
    print "\t".join(map(str,row))
    odp.createRecord(str(row[0]),str(row[1]))
    odp.createManifestLine(str(row[0]),str(row[1]))
odp.enditall()
# Create zip file here
