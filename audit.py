import xml.etree.cElementTree as ET
import re
from collections import defaultdict
import pprint


lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

OSM_FILE = "columbia.osm"  # Replace this with your osm file
SAMPLE_FILE = "sample.osm"

k = 10 # Parameter: take every k-th top level element

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Crossing", "Route", "Highway", "Way", "Plaza", "Path",
            "Alley", "Circle", "Trace", "Loop", "Walk", "Pass", "Terrace", "Cove", "Run"]

mapping = { "St": "Street", "St.": "Street", "Ave": "Avenue", "Rd.": "Road", 
            "Rd" : "Road", "Hwy": "Highway", "Dr": "Drive", "Xing": "Crossing",
            "Ln": "Lane",  "Pl": "Plaza", "Plz": "Plaza",
            "Trl": "Trail", "Sq": "Square", "Aly": "Alley", "Cir": "Circle",
            "Trc": "Trace", "Trce": "Trace", "Rte": "Route", "Pky": "Parkway",  
            "Blvd": "Boulevard", "Ter": "Terrace", "Cv": "Cove", "Ct": "Court"
          }

"""
This counts the different tags in a given file. 
"""
def count_tags(filename):
    d = dict()
    for event, elem in ET.iterparse(filename):
        if elem.tag in d:
            d[elem.tag] += 1
        else:
            d[elem.tag] = 1    
    return d

tags = count_tags('columbia.osm')
pprint.pprint(tags)

"""
These two blocks write a sample file, using 
the global k above to pick out top-level elements. 
"""
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag
    """
    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


with open(SAMPLE_FILE, 'wb') as output:
    output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    output.write('<osm>\n  ')

    # Write every kth top level element
    for i, element in enumerate(get_element(OSM_FILE)):
        if i % k == 0:
            output.write(ET.tostring(element, encoding='utf-8'))

    output.write('</osm>')

"""
These functions count anomalies in all 'tag' attributes. 
Two of these (lower_colon and problemchars) will 
be targets for cleaning). 	
"""	
def count_type(element, types, attrib):
    if element.tag == "tag":
        a = element.attrib[attrib]
        l = lower.search(a)
        lc = lower_colon.search(a)
        p = problemchars.search(a)
        if l:
            types['lower'] += 1
        if lc: 
            types['lower_colon'] += 1
        if p: 
            types['problemchars'] += 1
    return types



def count_types_in_file(filename, attrib):
    types = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        count = count_type(element, types, attrib)

    return count	
	
	
"""
These functions were used to audit the street names. 
They had to be run repeatedly to get the mapping list that 
appears at the top of the file. 
"""
def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        #print "Street Type: ", street_type
        if street_type not in expected:
            street_types[street_type].add(street_name)
			
def is_street_name(elem):
    return (elem.attrib['k'] == "tiger:name_type")	

            
def update_name(name, mapping):
    m = street_type_re.search(name)
    if m:
        street_type = m.group()
        name = name.replace(street_type, mapping[street_type])
    return name


def audit_streets(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types	
	