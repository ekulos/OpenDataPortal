import sys

import urllib,urllib2

query = { 'query':"""
PREFIX a: <http://www.eea.europa.eu/portal_types/Data#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX ecodp: <http://ec.europa.eu/open-data/ontologies/ec-odp#>
PREFIX dcat: <http://www.w3.org/ns/dcat#>

CONSTRUCT {
 ?subj a dcat:Dataset;
       dct:publisher <http://publications.europa.eu/resource/authority/corporate-body/EEA>;
       ecodp:datasetStatus <http://ec.europa.eu/open-data/kos/dataset-status/Completed>;
       dct:license <http://creativecommons.org/licenses/by/2.5/dk/>;
       dct:title ?title;
       dct:description ?description;
       dct:identifier ?id;
       dct:issued ?effective;
       dct:modified ?modified;
       ecodp:keyword ?theme;
       dct:spatial `IF(bound(?countrycode),IRI(bif:concat('http://publications.europa.eu/resource/authority/ntu/', bif:upper(?countrycode))),?countrycode)`.
 ?subj dcat:distribution ?subj .
 ?subj dcat:accessURL ?subj;
     a <http://www.w3.org/TR/vocab-dcat#Download>;
     ecodp:distributionFormat "text/html"
}
WHERE {
 {
  ?subj a a:Data ;
        a:id ?id;
        dct:title ?title
  OPTIONAL { ?subj dct:description ?description }
  OPTIONAL { ?subj dct:effective ?effective }
  OPTIONAL { ?subj dct:modified ?modified }
  OPTIONAL { ?subj a:themes ?theme }
 } UNION {
     ?subj a a:Data ;
           a:geographicCoverage ?countrycode . 
 }
 FILTER (?subj = <http://www.eea.europa.eu/data-and-maps/data/european-red-lists> )
}
""",
'format':'application/xml' }

url = "http://semantic.eea.europa.eu/sparql?" + urllib.urlencode(query)

opener = urllib2.build_opener(urllib2.HTTPHandler)
urllib2.install_opener(opener)
req = urllib2.Request(url)
req.add_header("Accept", "application/xml")
conn = urllib2.urlopen(req)

if not conn:
    raise IOError, "Failure in open"

data = conn.read(8192)
while data:
    sys.stdout.write(data)
    data = conn.read(8192)
conn.close()
