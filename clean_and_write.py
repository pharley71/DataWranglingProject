import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus

import schema

OSM_PATH = "columbia.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Crossing", "Route", "Highway", "Way", "Plaza", "Path",
            "Alley", "Circle", "Trace", "Loop", "Walk", "Pass", "Terrace", "Cove", "Run", "Pass"]

mapping = { "St": "Street", "St.": "Street", "Ave": "Avenue", "Rd.": "Road", 
            "Rd" : "Road", "Hwy": "Highway", "Dr": "Drive", "Xing": "Crossing",
            "Ln": "Lane",  "Pl": "Plaza", "Plz": "Plaza", "Way": "Way",
            "Trl": "Trail", "Sq": "Square", "Aly": "Alley", "Cir": "Circle",
            "Trc": "Trace", "Trce": "Trace", "Rte": "Route", "Pky": "Parkway",  
            "Blvd": "Boulevard", "Ter": "Terrace", "Cv": "Cove", "Ct": "Court", 
            "Loop": "Loop", "Pass": "Pass", "Path": "Path", "Run": "Run", 
            "Fwy": "Freeway", "Walk": "Walk"
          }

city_list = ["Columbia", "West Columbia", "Forest Acres", "Irmo"]

city_mapping = { "Columbia, SC" : "Columbia", "W. Columbia" : "West Columbia", 
                 "Fort Jackson": "Columbia" }		  

# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()     
            
def update_name(name, mapping):
    m = street_type_re.search(name)
    if m:
        street_type = m.group()
        name = name.replace(street_type, mapping[street_type])
    return name
	
def update_city(name, mapping, list): 
    if name not in list: 
        name = mapping[name]:      	
    return name 
	
def is_street_name(elem):
    return (elem.attrib['k'] == "tiger:name_type") 

def is_city_name(elem):
    return (elem.attrib['k'] == "addr:city")	
            
def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    if element.tag == "node":
        for field in node_attr_fields:
            node_attribs[field] = element.attrib[field]
            
    if element.tag == "way":
        for field in way_attr_fields: 
            way_attribs[field] = element.attrib[field]
        nd_check = element.find("nd")
        if nd_check is None: 
            pass 
        else: 
            position = 0
            for tag in element.iter("nd"):
                way_node = dict()
                way_node['id'] = element.attrib['id']
                way_node['node_id'] = tag.attrib['ref']
                way_node['position'] = position
                way_nodes.append(way_node)
                position += 1             
            
    tag_check = element.find("tag")
    if tag_check is None: 
        pass
    else: 
        for tag in element.iter("tag"):
            n = PROBLEMCHARS.search(tag.attrib['k'])
            if is_street_name(tag): 
                tag.attrib['v'] =  update_name(tag.attrib['v'], mapping)
			elif is_city_name(tag): 
                tab.attrib['v'] = update_city(tag.attrib['v'], city_mapping, city_list)  			
            if n: 
                pass
            else: 
                new_tag = dict()
                new_tag['id'] = element.attrib['id']
                new_tag['value'] = tag.attrib['v']
                m = LOWER_COLON.search(tag.attrib['k'])
                if m: 
                    new_tag['key'] = tag.attrib['k'].split(":",1)[1]
                    new_tag['type'] = tag.attrib['k'].split(":",1)[0]
                else:
                    new_tag['key'] = tag.attrib['k']
                    new_tag['type'] = 'regular'
                tags.append(new_tag)
        
    if element.tag == 'node':
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}  

def validate_element(element, validator, schema=SCHEMA):
    #Raise ValidationError if element does not match schema
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))

def validate_sample(samplefile):
    validator = cerberus.Validator()
    for element in get_element(samplefile, tags=('node', 'way')):
        el = shape_element(element)
        if el:
            validate_element(el, validator)


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'wb') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'wb') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'wb') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'wb') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'wb') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    validate_sample("smallsample.osm")
    process_map(OSM_PATH)
