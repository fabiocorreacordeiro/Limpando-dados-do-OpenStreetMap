
# coding: utf-8

# ** UDACITY **
# 
# ** Nanodegree Analista de Dados **
# 
# ### Projeto: Limpando dados do OpenStreetMap
# 
# # Baía de Guanabara, Rio de Janeiro - Brasil
# 
# **por Fábio Corrêa Cordeiro**

# Esse notebook contém os códigos necessários para a realizaçõ do projeto "P3: Limpando dados do OpenStreetMap" do Nanodegree Analista de Dados. Serão utilizados os mesmo código utilizados na lição 18 "Estudo de Caso: Dados do Street Map" com as devidas alterações necessárias

# In[13]:


import xml.etree.cElementTree as ET
import pprint
import re
from collections import defaultdict
import codecs
import json
from pymongo import MongoClient

""" Choosing dataset """
# test file
#filename = 'Jardim_Guanabara_OSM'

# test file2
#filename = 'Niteroi OSM.osm'

# original file
filename = 'Guanabara_Bay_OSM'


# ### 3 Quiz: Tratamento iterativo
# 
# *Your task is to use the iterative parsing to process the map file and find out not only what tags are there, but also how many, to get the feeling on how much of which data you can expect to have in the map. Fill out the count_tags function. It should return a dictionary with the tag name as the key and number of times this tag can be encountered in 
# the map as value.*
# 
# *Note that your code will be tested with a different data file than the 'example.osm'*

# In[14]:

def count_tags(filename):
    """ For a given file this function returns a dictionary of types of tags and number of elements. """
    tree = ET.parse(filename)
    root = tree.getroot()
    data = {}
    for leaf in root.iter():
        if leaf.tag not in data:
            data[leaf.tag]=1
        else:
            data[leaf.tag]+=1
    return data

tags = count_tags(filename)
print tags


# ### 4 Quiz: Modelo de Dados
# 
# *Your task is to explore the data a bit more. Before you process the data and add it into your database, you should check the
# "k" value for each "<tag>" and see if there are any potential problems.*
# 
# *We have provided you with 3 regular expressions to check for certain patternsin the tags. As we saw in the quiz earlier, we would like to change the datamodel and expand the "addr:street" type of keys to a dictionary like this:*
# 
# *{"address": {"street": "Some value"}}*
# 
# *So, we have to see if we have such tags, and if we have any tags withproblematic characters.*
# 
# *Please complete the function 'key_type', such that we have a count of each of four tag categories in a dictionary:*
#   * *"lower", for tags that contain only lowercase letters and are valid,*
#   * *"lower_colon", for otherwise valid tags with a colon in their names,*
#   * *"problemchars", for tags with problematic characters, and*
#   * *"other", for other tags that do not fall into the other three categories.*
# *See the 'process_map' and 'test' functions for examples of the expected format.*

# In[15]:

""" Regular expression for identification of lower caps, colons and other problem characters. """
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


def key_type(element, keys):
    """ 
    This function identify if a element has lower caps, colons, problem characters
    and other characters, and update the key dictionary.
    """
    if element.tag == "tag":
        if lower.search(element.attrib['k']) != None:
            keys["lower"] += 1
        else:
            if lower_colon.search(element.attrib['k']) != None:
                keys["lower_colon"] += 1
            else:    
                if problemchars.search(element.attrib['k']) != None:
                    keys["problemchars"] += 1
                else:
                    keys["other"] += 1
    return keys

def process_map(filename):
    """
    For a file, return a dictionary of how many elements has lower caps, colons, problem characters
    and other characters
    """
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)
    return keys

keys = process_map(filename)
print keys


# ### 8 Quiz: Investigando usuários
# 
# *Your task is to explore the data a bit more.*
# *The first task is a fun one - find out how many unique users*
# *have contributed to the map in this particular area!*
# 
# *The function process_map should return a set of unique user IDs ("uid")*

# In[16]:

def get_user(element):
    """ For an element gets the attribute 'user'. """
    try:
        return element.attrib['user']
    except:
        return


def process_map(filename):
    """ For a file, parses all element and return a set of list of users. """
    users = set()
    for _, element in ET.iterparse(filename):
        if get_user(element) != None:
            users.add(get_user(element))
    return users

users = process_map(filename)
print 'N° unique user IDs: ', len(users)


# ### 11 Quiz: Melhorando o nome das ruas
# 
# *Your task in this exercise has two steps:*
# 
# - *audit the OSMFILE and change the variable 'mapping' to reflect the changes needed to fix* 
#     *the unexpected street types to the appropriate ones in the expected list.*
#     *You have to add mappings only for the actual problems you find in this OSMFILE,*
#     *not a generalized solution, since that may and will depend on the particular area you are auditing.*
# - *write the update_name function, to actually fix the street name.*
#     *The function takes a string with street name as an argument and should return the fixed name*
#     *We have provided a simple test so that you see what exactly is expected*

# In[17]:

""" This regular expression has been changed to capture the first word and not the last one. """
street_type_re = re.compile(r'^\S+\b', re.IGNORECASE)


""" Updated list with the "street_types" found on the Guanabara Bay map. """
expected = ["Rua", "Avenida", "Quadra", "Via", "Estrada", "Caminho", "Estacionamento", "Parque", "Praia",
           "Alameda","Beco","Campo", "Ladeira", "Largo", "Mirante", "Rodovia", "Travessa", "Praça", 'Boulevard',
           "Calçadão" ,"Condomínio"]

""" Mapping updated with the errors and abbreviations found on the Guanabara Bay map. """
mapping = { 
            'Av ': "Avenida ",
            'Av. ': "Avenida ",
            'PLAZA ': "Praça ",
            'Pca ': "Praça ",
            'Praca ': "Praça ",
            'R. ': "Rua ",
            'R ': "Rua ",
            'Rue ': "Rua ",
            'rua ': "Rua ",
            'Rod ': "Rodovia ",
            'Rod. ': "Rodovia ",
            'Trav ': "Travessa "
            }
          

"""
It was necessary to add ".encode ('utf8')" in the comparison of strings
of the function "audit_street_type" due to the special characters
of the Portuguese language.
"""
def audit_street_type(street_types, street_name):
    """ For a given dictionary of street_types and a street name returns the dictionary updated. """
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type.encode('utf8') not in expected:
            street_types[street_type].add(street_name)
            return street_types


def is_street_name(elem):
    """ Returns True if attrib['k'] of an element is "addr:street". """
    return (elem.attrib['k'] == "addr:street")


def audit(osmfile):
    """ For a given file returns a dictionary with the "street_types". """
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
                    tag.attrib['v'] = update_name(tag.attrib['v'], mapping)
    osm_file.close()
    return street_types


def update_name(name, mapping):
    """ Update the street name using the mapping dictionary. """
    for target_name in mapping:
        if name.find(target_name) != -1:
            a = name[:name.find(target_name)]
            b = mapping[target_name]
            c = name[name.find(target_name)+len(target_name):]
            name = a + b + c
    return name

st_types = audit(filename)

for st_type, ways in st_types.iteritems():
    for name in ways:
        better_name = update_name(name, mapping)
        print name, "=>", better_name


# Além de verificar os nomes das ruas, como solicitado no exercício, resolvermos auditar o nome das cidades.

# In[18]:

""" Mapping2 updated with the errors in the city found on the Guanabara Bay map. """

mapping2 = {'Camboinha': 'Niterói',
            'Camboinhas': 'Niterói',
            'Caramujo': 'Niterói',
            'Várzea das Moças, São Gonçalo': 'São Gonçalo',
            'rio de Janeiro': 'Rio de Janeiro',
            'SãoGonçalo': 'São Gonçalo',
            'Maracanã': 'Rio de Janeiro',
            'Rio de janeiro': 'Rio de Janeiro',
            'Leblon': 'Rio de Janeiro',
            'niterói': 'Niterói',
            'Colubandê': 'São Gonçalo',
            'Fonseca': 'Niterói',
            'Niteroi': 'Niterói',
            'rio de janeiro': 'Rio de Janeiro',
            'Alcântara': 'São Gonçalo',
            'niteroi': 'Niterói',
            'Cafubá': 'Niterói',
            'RIo de Janeiro': 'Rio de Janeiro',
            'Rua Monsenhor Magaldi': 'Rio de Janeiro',
            'Rio de Janeiro,': 'Rio de Janeiro',
            'Méier': 'Rio de Janeiro',
            'São Lourenço': 'Niterói',
           }

def update_city(city, mapping2):
    """ For a given city return the correct city name using "mapping2". """
    try:
        city = city.encode('utf8')
    except:
        pass
    if city in mapping2:
        city = mapping2[city.decode('utf8').encode('utf8')]
    return city
    


osm_file = open(filename, "r")
cities = []
for event, elem in ET.iterparse(osm_file, events=("start",)):
    for tag in elem.iter("tag"):
        if tag.attrib['k'] == "addr:city":
            tag.attrib['v'] = update_city(tag.attrib['v'], mapping2)
            cities.append(tag.attrib['v'])
osm_file.close()
print set(cities)


# ### 12 Quiz: Preparando-se para o Banco de Dados
# 
# *Your task is to wrangle the data and transform the shape of the data*
# *into the model we mentioned earlier. The output should be a list of dictionaries*
# *that look like this:*

# *{
# "id": "2406124091",
# "type: "node",
# "visible":"true",
# "created": {
#           "version":"2",
#           "changeset":"17206049",
#           "timestamp":"2013-08-03T16:43:42Z",
#           "user":"linuxUser16",
#           "uid":"1219059"
#         },
# "pos": [41.9757030, -87.6921867],
# "address": {
#           "housenumber": "5157",
#           "postcode": "60625",
#           "street": "North Lincoln Ave"
#         },
# "amenity": "restaurant",
# "cuisine": "mexican",
# "name": "La Cabana De Don Luis",
# "phone": "1 (773)-271-5176"
# }*

# *You have to complete the function 'shape_element'.*
# *We have provided a function that will parse the map file, and call the function with the element
# as an argument. You should return a dictionary, containing the shaped data for that element.
# We have also provided a way to save the data in a file, so that you could use
# mongoimport later on to import the shaped data into MongoDB.*
# 
# *Note that in this exercise we do not use the 'update street name' procedures
# you worked on in the previous exercise. If you are using this code in your final
# project, you are strongly encouraged to use the code from previous exercise to 
# update the street names before you save them to JSON.* 
# 
# *In particular the following things should be done:*
# - *you should process only 2 types of top level tags: "node" and "way"*
# - *all attributes of "node" and "way" should be turned into regular key/value pairs, except:*
#     - *attributes in the CREATED array should be added under a key "created"*
#     - *attributes for latitude and longitude should be added to a "pos" array,
#       for use in geospacial indexing. Make sure the values inside "pos" array are floats
#       and not strings.*
# - *if the second level tag "k" value contains problematic characters, it should be ignored*
# - *if the second level tag "k" value starts with "addr:", it should be added to a dictionary "address"*
# - *if the second level tag "k" value does not start with "addr:", but contains ":", you can
#   process it in a way that you feel is best. For example, you might split it into a two-level
#   dictionary like with "addr:", or otherwise convert the ":" to create a valid key.*
# - *if there is a second ":" that separates the type/direction of a street,
#   the tag should be ignored, for example:*
# 
# <tag k="addr:housenumber" v="5158"/>
# <tag k="addr:street" v="North Lincoln Avenue"/>
# <tag k="addr:street:name" v="Lincoln"/>
# <tag k="addr:street:prefix" v="North"/>
# <tag k="addr:street:type" v="Avenue"/>
# <tag k="amenity" v="pharmacy"/>
# 
#   *should be turned into:*
# 
# *{...
# "address": {
#     "housenumber": 5158,
#     "street": "North Lincoln Avenue"
# }
# "amenity": "pharmacy",
# ...
# }*
# 
# - *for "way" specifically:*
# 
#   <nd ref="305896090"/>
#   <nd ref="1719825889"/>
# 
# *should be turned into*
# "node_refs": ["305896090", "1719825889"]
# """

# In[19]:

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]


def shape_element(element):
    """ For a given element, returns a dictionary with the requested shape. """
    node = {}
    if element.tag == "node" or element.tag == "way" :
        node['id'] = element.attrib['id']
        if element.tag == "node":
            node['type'] = 'node'
        if element.tag == "way":
            node['type'] = 'way'
            node['node_refs'] = []
        try:
            node["visible"] = element.attrib["visible"]
        except:
            pass
        node["created"] = {}
        node["created"]['version'] = element.attrib['version']
        node["created"]['changeset'] = element.attrib['changeset']
        node["created"]['timestamp'] = element.attrib['timestamp']
        node["created"]['user'] = element.attrib['user']
        node["created"]['uid'] = element.attrib['uid']
        if element.tag == "node":
            node["pos"] = [float(element.attrib['lat']),float(element.attrib['lon'])]
        node["address"] = {}
        for tag in element.iter('tag'):
            if problemchars.search(tag.attrib['k']) == None:
                if tag.attrib['k'] == "addr:housenumber":
                    node["address"]["housenumber"] = tag.attrib['v']
                if tag.attrib['k'] == "addr:postcode":
                    node["address"]["postcode"] = tag.attrib['v']
                if tag.attrib['k'] == "addr:street":
                    node["address"]["street"] = update_name(tag.attrib['v'], mapping)
                if tag.attrib['k'] == "addr:city":
                    node["address"]["city"] = update_city(tag.attrib['v'], mapping2)
                if tag.attrib['k'] == "addr:amenity":
                    node["amenity"] = tag.attrib['v']
                if tag.attrib['k'] == "addr:cuisine":
                    node["cuisine"] = tag.attrib['v']
                if tag.attrib['k'] == "addr:name":
                    node["name"] = tag.attrib['v']
                if tag.attrib['k'] == "addr:phone":
                    node["phone"] = tag.attrib['v']
        if node["address"] == {}:
            node.pop('address',None)
        for tag in element.iter('nd'):        
            node['node_refs'].append(tag.attrib['ref'])
        return node
    else:
        return None

def process_map(file_in, pretty = False):
    """ For a given file, saves a JSON file with the requested shape and returns a newly shaped data. """
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

    # NOTE: if you are running this code on your computer, with a larger dataset, 
    # call the process_map procedure with pretty=False. The pretty=True option adds 
    # additional spaces to the output, making it significantly larger.
data = process_map(filename, False)


# ### Carregando os dados no Banco de Dados e realizando consultas
# 
# Nesse momento iremos conectar com o banco de dados MongoDB e importaremos o arquivo JSON.

# In[20]:

client = MongoClient('mongodb://localhost:27017')
db = client.project
db.OSM.insert_many(data)


# A partir de agora serão realizadas algumas consultas:
# 
# Número de documentos e tamanho da base

# In[21]:

collstats = db.command("collstats",'OSM')
print 'count: ', collstats['count']
print 'size: ', collstats['size']


# Número de vias ("way")

# In[22]:

query = {'type': 'way'}
print db.OSM.find(query).count()


# Número de nós ("node")

# In[23]:

query = {'type': 'node'}
print db.OSM.find(query).count()


# Número de nós em algumas ruas famosas

# In[25]:

def street_nodes(street_name):
    query = {'address.street': street_name, 'type': 'node'}
    return db.OSM.find(query).count()
street_nodes("Avenida Presidente Vargas")


# In[26]:

street_nodes("Avenida Brasil")


# In[27]:

street_nodes('Calçadão de Copacabana')


# In[28]:

street_nodes('Avenida Atlântica')


# In[29]:

street_nodes('Avenida Rio Branco')


# Número de usuários distintos que criaram vias ("way") ou nós ("node").

# In[30]:

print len(db.OSM.distinct('created.uid'))

