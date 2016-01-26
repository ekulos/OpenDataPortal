# -*- coding: utf-8 -*-

import sys,time
import urllib,urllib2
import sparql

def reduce_to_length(text, max_length):
    parts = text.split("-")
    reduced_text = ""
    for i in range(1, len(parts) + 1):
        tmp_reduced_text = "-".join(parts[0:i])
        if len(tmp_reduced_text) < max_length:
            reduced_text = tmp_reduced_text
    return reduced_text

class OpenDataPortal:

    license = 'http://opendatacommons.org/licenses/by/'
    odp_license = 'http://open-data.europa.eu/kos/licence/EuropeanCommission'
    publisher = 'http://publications.europa.eu/resource/authority/corporate-body/EEA'
    datasetStatus = 'http://ec.europa.eu/open-data/kos/dataset-status/Completed'

    contactPoint = 'http://www.eea.europa.eu/address.html'
    contactPoint_type = 'http://xmlns.com/foaf/0.1/Agent'
    foaf_phone = 'tel:+4533367100'
    foaf_name = 'European Environment Agency'
    ecodp_contactAddress = 'Kongens Nytorv 6, 1050 Copenhagen K, Denmark'
    foaf_workplaceHomepage = 'http://www.eea.europa.eu'

    def __init__(self, endpoint):
       self.endpoint = endpoint
       self.manifestnum = 0
       self.manifestf = open('manifest.xml','w')
       self.manifestf.write("""<?xml version="1.0" encoding="UTF-8"?>
<ecodp:manifest
	xmlns:ecodp="http://open-data.europa.eu/ontologies/ec-odp#"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xsi:schemaLocation="http://open-data.europa.eu/ontologies/protocol-v2.0/odp-protocol.xsd"
	ecodp:version="2.0"
	ecodp:package-id="EEA"
	ecodp:creation-date-time="%s"
	ecodp:publisher="%s"
	ecodp:priority="normal">
""" % (time.strftime("%Y-%m-%dT%H:%M:%S"), self.publisher))

    def createRemoveLine(self, dataseturi, identifier):
        """ Create an action to remove the record from the ODP database"""
        self.manifestnum += 1
        self.manifestf.write("""<ecodp:action ecodp:id="rm%d" ecodp:object-uri="%s" ecodp:object-type="dataset">
		<ecodp:remove/>
	</ecodp:action>\n""" % (self.manifestnum, dataseturi))

    def createAddReplaceLine(self, dataseturi, identifier, ckan_name):
        """ Create an action to replace or add the record """
        self.manifestnum += 1
        self.manifestf.write("""<ecodp:action ecodp:id="add%d" ecodp:object-uri="%s" ecodp:object-type="dataset" ecodp:object-ckan-name="%s">
		<ecodp:add-replace ecodp:object-status="published"  ecodp:package-path="/datasets/%s.rdf"/>
	</ecodp:action>\n""" % (self.manifestnum, dataseturi, ckan_name, identifier))

    def enditall(self):
        self.manifestf.write("""</ecodp:manifest>\n""")
        self.manifestf.close()

# http://www.eea.europa.eu/data-and-maps/data/urban-atlas
# For examples of datafilelink see http://www.eea.europa.eu/data-and-maps/data/urban-atlas/germany/@@rdf
# For examples of sparql queries see http://www.eea.europa.eu/data-and-maps/data/biogeographical-regions-europe/codelist-for-bio-geographical-regions/@@rdf

    def datasetQuery(self, old=False):
        datafile = """
?datatable dct:hasPart ?datafile.
   {
     {
       SELECT DISTINCT ?datafile STRDT(bif:concat(?datafile,'/at_download/file'), xsd:anyURI) AS ?downloadUrl ?format
       WHERE {
         ?datafile a datafile:DataFile;
                   dct:format ?format
         filter(str(?format) = "application/zip")
       }
     }
   } UNION {
     {
       SELECT DISTINCT ?datafile STRDT(bif:concat(?datafile,'/at_download/file'), xsd:anyURI) AS ?downloadUrl ?format
       WHERE
       {
         { SELECT DISTINCT ?datafile count(?format) as ?formatcnt
           WHERE {
             ?datafile a datafile:DataFile;
             dct:format ?format
             FILTER (str(?format) != 'application/zip')
           }
         } . FILTER (?formatcnt = 1)
         ?datafile dct:format ?format
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
   } UNION {
     {
       SELECT DISTINCT ?datafile STRDT(bif:concat(?datafile,'/download.csv'), xsd:anyURI) AS ?downloadUrl 'text/csv' as ?format
       WHERE {
         ?datafile a sparql:Sparql
       }
     }
   } UNION {
     {
       SELECT DISTINCT ?datafile STRDT(?datafile, xsd:anyURI) AS ?downloadUrl "file" as ?format
       WHERE {
         ?datafile a file:File
       }
     }
   }
   ?datafile dct:title    ?dftitle .
   ?datafile dct:modified ?dfmodified
"""
    
        if old:
            datafile = ""
        
        return """
PREFIX a: <http://www.eea.europa.eu/portal_types/Data#>
PREFIX dt: <http://www.eea.europa.eu/portal_types/DataTable#>
PREFIX org: <http://www.eea.europa.eu/portal_types/Organisation#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX ecodp: <http://open-data.europa.eu/ontologies/ec-odp#>
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX datafilelink: <http://www.eea.europa.eu/portal_types/DataFileLink#>
PREFIX datafile: <http://www.eea.europa.eu/portal_types/DataFile#>
PREFIX sparql: <http://www.eea.europa.eu/portal_types/Sparql#>
PREFIX file: <http://www.eea.europa.eu/portal_types/File#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX cr: <http://cr.eionet.europa.eu/ontologies/contreg.rdf#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

CONSTRUCT {
 ?dataset a dcat:Dataset;
       dct:publisher <%s>;
       ecodp:datasetStatus <%s>;
       dct:license <%s>;
       dct:license ?odp_license;
       dct:title ?title;
       dct:description ?description;
       dct:identifier '%s';
       ecodp:ckan-name '%s';
       dct:issued ?effective;
       dct:modified ?modified;
       ecodp:keyword ?theme;
       dct:spatial ?pubspatial;
       dct:subject ?subject;
       dcat:theme ?dcat_theme;
       dct:isReplacedBy ?isreplaced;
       dct:replaces ?replaces;

       ecodp:contactPoint ?ecodp_contactPoint .
       ?ecodp_contactPoint  rdf:type ?ecodp_contactPoint_type .
       ?ecodp_contactPoint  foaf:phone ?foaf_phone .
       ?ecodp_contactPoint  foaf:name  ?foaf_name .
       ?ecodp_contactPoint  ecodp:contactAddress ?ecodp_contactAddres .
       ?ecodp_contactPoint foaf:workplaceHomepage ?foaf_workplaceHomepage.

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
   OPTIONAL { ?dataset dct:isReplacedBy ?isreplaced }
   OPTIONAL { ?dataset dct:replaces ?replaces }
   
   {select (<%s> as ?ecodp_contactPoint) where {}}
   {select (<%s> as ?ecodp_contactPoint_type) where {}}
   {select ("%s" as ?foaf_phone) where {}}
   {select ("%s"@en as ?foaf_name) where {}}
   {select ("%s"@en as ?ecodp_contactAddres) where {}}
   {select (<%s> as ?foaf_workplaceHomepage) where {}}

   {select (STRDT("%s", skos:Concept) as ?odp_license) where {}}
    """ + datafile + """
  } UNION {
   ?dataset dct:subject ?subject
  } UNION {
   ?dataset dct:subject ?theme  FILTER (isLiteral(?theme) && !REGEX(?theme,'[()/]'))
  } UNION {
   ?dataset dct:spatial ?spatial .
   ?spatial owl:sameAs ?pubspatial
        FILTER(REGEX(?pubspatial, '^http://publications.europa.eu/resource/authority/country/'))
  } UNION {
    ?dataset cr:tag ?tag.
      ?dcat_theme a skos:Concept.
      ?dcat_theme rdfs:label ?tag.
  }
  FILTER (?dataset = <%s> )
}
"""
    def createDSRecord(self, dataseturi, identifier, ckan_name, old=False):
        """ Record for normal datasets"""
        self.createRecord(dataseturi, identifier, self.datasetQuery(old), ckan_name)

    rdfDatasetQuery = """
PREFIX void: <http://rdfs.org/ns/void#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX org: <http://www.eea.europa.eu/portal_types/Organisation#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX ecodp: <http://open-data.europa.eu/ontologies/ec-odp#>
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

CONSTRUCT {
 ?dataset a dcat:Dataset;
       dct:publisher <%s>;
       ecodp:datasetStatus <%s>;
       dct:license <%s>;
       dct:license ?odp_license;
       dct:title ?title;
       dct:description ?description;
       dct:identifier '%s';
       ecodp:ckan-name '%s';
       dct:issued ?effective;
       dct:modified ?modified;
       ecodp:keyword ?theme;
       dct:spatial ?pubspatial;
       dct:subject <http://eurovoc.europa.eu/100155>;
       dcat:theme ?dcat_theme;

       ecodp:contactPoint ?ecodp_contactPoint .
       ?ecodp_contactPoint  rdf:type ?ecodp_contactPoint_type .
       ?ecodp_contactPoint  foaf:phone ?foaf_phone .
       ?ecodp_contactPoint  foaf:name  ?foaf_name .
       ?ecodp_contactPoint  ecodp:contactAddress ?ecodp_contactAddres .
       ?ecodp_contactPoint foaf:workplaceHomepage ?foaf_workplaceHomepage.

 ?dataset dcat:distribution ?datafile .
 ?datafile dcat:accessURL ?downloadUrl.
 ?datafile a <http://www.w3.org/TR/vocab-dcat#Download>;
       ecodp:distributionFormat 'application/rdf+xml';
       dct:description ?dftitle;
       dct:modified ?dfmodified
}
WHERE {
  {
   ?dataset a void:Dataset ;
        dct:title ?title
   OPTIONAL { ?dataset dct:description ?description }
   OPTIONAL { ?dataset dct:issued ?effective }
   OPTIONAL { ?dataset dct:modified ?modified }

   
   {select (<%s> as ?ecodp_contactPoint) where {}}
   {select (<%s> as ?ecodp_contactPoint_type) where {}}
   {select ("%s" as ?foaf_phone) where {}}
   {select ("%s"@en as ?foaf_name) where {}}
   {select ("%s"@en as ?ecodp_contactAddres) where {}}
   {select (<%s> as ?foaf_workplaceHomepage) where {}}

   {select (STRDT("%s", skos:Concept) as ?odp_license) where {}}
   ?dataset void:subset ?datafile.
   {
       SELECT DISTINCT ?datafile STRDT(?remoteUrl, xsd:anyURI) AS ?downloadUrl 
       WHERE {
         ?datafile a void:Dataset;
                   void:dataDump ?remoteUrl
       }
   }
   ?datafile dct:title    ?dftitle
   OPTIONAL { ?datafile dct:modified ?dfmodified }
} UNION {
   ?dataset dct:subject ?dbpsubject.
   ?dbpsubject rdfs:label ?theme FILTER(LANG(?theme) = 'en')
} UNION {
      ?dataset dct:subject ?subject.
      ?subject rdfs:label ?subject_label.
      ?dcat_theme a skos:Concept.
      ?dcat_theme rdfs:label ?subject_label.
  }
  FILTER (?dataset = <%s> )
}
"""

    def createRdfRecord(self, dataseturi, identifier, ckan_name):
        """ Record for RDF datasets"""
        self.createRecord(dataseturi, identifier, self.rdfDatasetQuery, ckan_name)

    def createRecord(self, dataseturi, identifier, datasetQuery, ckan_name):
        query = { 'query': datasetQuery % (self.publisher,
                                            self.datasetStatus,
                                            self.license,
                                            identifier,
                                            ckan_name,
                                            self.contactPoint,
                                            self.contactPoint_type,
                                            self.foaf_phone,
                                            self.foaf_name,
                                            self.ecodp_contactAddress,
                                            self.foaf_workplaceHomepage,
                                            self.odp_license,
                                            dataseturi),
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
    _listCurrentDS = """
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

    def queryCurrentDS(self):
        """ Find current datasets and create metadata records for them """
        result = sparql.query(self.endpoint, self._listCurrentDS)
        for row in result.fetchall():
            print "\t".join(map(str,row))
            ckan_name = "%s_%s" %(str(row[0]).split("/")[-2], str(row[1]))
            ckan_name = reduce_to_length(ckan_name, 100)
            self.createDSRecord(str(row[0]),str(row[1]), ckan_name, old=False)
            self.createAddReplaceLine(str(row[0]),str(row[1]), ckan_name)
            
#------------------------
    _listOldDS = """
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
  FILTER(BOUND(?isreplaced))
}
"""
# FILTER (?dataset = <http://www.eea.europa.eu/data-and-maps/data/fluorinated-greenhouse-gases-aggregated-data-1> )  
    def queryOldDS(self):
        """ Find datasets and create metadata records for them """
        result = sparql.query(self.endpoint, self._listOldDS)
        for row in result.fetchall():
            print "\t".join(map(str,row))
            ckan_name = "%s_%s" %(str(row[0]).split("/")[-2], str(row[1]))
            ckan_name = reduce_to_length(ckan_name, 100)
            self.createDSRecord(str(row[0]),str(row[1]), ckan_name, old=True)
            self.createAddReplaceLine(str(row[0]),str(row[1]), ckan_name)

    #
    # List datasets that have become obsolete. We must tell ODP to remove them
    #
    _listObsoleteDS = """
PREFIX a: <http://www.eea.europa.eu/portal_types/Data#>
PREFIX dct: <http://purl.org/dc/terms/>
SELECT DISTINCT ?dataset ?id
WHERE {
  ?dataset a a:Data ;
        a:id ?id;
        dct:description ?description;
        dct:hasPart ?datatable.
  ?dataset dct:isReplacedBy ?isreplaced.
  ?datatable dct:hasPart ?datafile.
}
"""

    def queryObsoleteDS(self):
        result = sparql.query("http://semantic.eea.europa.eu/sparql", self._listObsoleteDS)
        for row in result.fetchall():
            print "\t".join(map(str,row))
            self.createRemoveLine(str(row[0]),str(row[1]))
    #
    # Find VoID datasets
    #
    _listCurrentVoid = """
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX void: <http://rdfs.org/ns/void#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

SELECT DISTINCT ?dataset (bif:subseq(str(?dataset),bif:__max_notnull(bif:strrchr(str(?dataset),'#'),bif:strrchr(str(?dataset),'/'))+1) AS ?id)
WHERE {
 ?dataset a void:Dataset;
            rdfs:label ?label FILTER(?label != '')
 ?dataset dcterms:creator ?creator.
 ?creator foaf:homepage ?homepage FILTER (?homepage IN (<http://www.eea.europa.eu/>, <http://www.eea.europa.eu>))
 ?dataset void:subset ?junior
}
"""
# OPTIONAL {?senior void:subset ?dataset }
# FILTER(!BOUND(?senior))
    def queryCurrentVoid(self):
        result = sparql.query(self.endpoint, self._listCurrentVoid)
        for row in result.fetchall():
            print "\t".join(map(str,row))
            ckan_name = "void_%s" %str(row[1])
            ckan_name = reduce_to_length(ckan_name, 100)
            self.createRdfRecord(str(row[0]),str(row[1]), ckan_name)
            self.createAddReplaceLine(str(row[0]),str(row[1]), ckan_name)


odp = OpenDataPortal("http://semantic.eea.europa.eu/sparql")
odp.queryCurrentDS()
odp.queryOldDS()
odp.queryCurrentVoid()
odp.queryObsoleteDS()
odp.enditall()

# Create zip file here
