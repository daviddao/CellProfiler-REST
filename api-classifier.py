from classifier_headless import *


# For test purposes
from cpa.properties import Properties
import cpa.dbconnect as dbconnect
from cpa.datamodel import DataModel

# For image processing
import cpa.imagetools as imagetools

import javabridge
import bioformats

# ----------------- Run -------------------

from flask import Flask, jsonify
from flask_restful import Resource, Api, reqparse

app = Flask(__name__)
api = Api(app)

# Cached Object
cached_json = {
    "base64": False,
    "json": ""
}

# Stores global settings
settings = {}


# Init
# p = Properties.getInstance()
# #p.LoadFile('/vagrant/data/23_classes/az-dnaonly.properties')
# p.LoadFile('/vagrant/data/5_classes/2010_08_21_Malaria_MartiLab_Test_2011_05_27_DIC+Alexa.properties')
# #p.LoadFile('/vagrant/data/cpa_example/example.properties')

# db = dbconnect.DBConnect.getInstance()
# dm = DataModel.getInstance()

# classifier = Classifier(properties=p) # Create a classifier with p
# #classifier.LoadTrainingSet('/vagrant/data/23_classes/Anne_DNA_66.txt')
# classifier.LoadTrainingSet('/vagrant/data/5_classes/MyTrainingSet_AllStages_Half.txt')
# #classifier.LoadTrainingSet('/vagrant/data/cpa_example/MyTrainingSet.txt')

# Starts CellProfiler Analyst
def start():
    # Init
    p = Properties.getInstance()
    p.LoadFile('/vagrant/data/23_classes/az-dnaonly.properties')
    #p.LoadFile('/vagrant/data/5_classes/2010_08_21_Malaria_MartiLab_Test_2011_05_27_DIC+Alexa.properties')
    #p.LoadFile('/vagrant/data/cpa_example/example.properties')

    db = dbconnect.DBConnect.getInstance()
    dm = DataModel.getInstance()

    classifier = Classifier(properties=p) # Create a classifier with p
    classifier.LoadTrainingSet('/vagrant/data/23_classes/Anne_DNA_66.txt')
    #classifier.LoadTrainingSet('/vagrant/data/5_classes/MyTrainingSet_AllStages_Half.txt')
    #classifier.LoadTrainingSet('/vagrant/data/cpa_example/MyTrainingSet.txt')

    settings['p'] = p
    settings['db'] = db
    settings['dm'] = dm
    settings['classifier'] = classifier


# Helper methods

# Structure of JSON which is sorted after table and images
#{ img_key: { images: {image_channel_color: img_path} ,obj_key: {class: label, x: cell_x, y: cell_y}}}
def calculateStructuredJSON():

    p = settings['p']
    dm = settings['dm']
    db = settings['db']
    classifier = settings['classifier']


    json = {}
    baseurl = p.image_url_prepend
    if baseurl == None:
        baseurl = ''
    image_channel_colors = p.image_channel_colors

    if p.table_id == None:
        json['merged_tables'] = False
        for label,objKey in classifier.trainingSet.entries:
            img_key = "image_" + str(objKey[0])
            obj_key = "object_" + str(objKey[1])

            if img_key not in json:
                json[img_key] = {}

            # Object key is hopefully unique for every unique image
            json[img_key][obj_key] = {}
            json[img_key][obj_key]['class'] = label
            json[img_key]['images'] = {}

            paths = db.GetFullChannelPathsForImage(objKey)
            for i,color in enumerate(image_channel_colors):
                json[img_key]['images'][color] = baseurl + paths[i]

    # We need to add a table key
    else:
        json['merged_tables'] = True
        for label,objKey in classifier.trainingSet.entries:
            table_key = "table_" + str(objKey[0])
            img_key = "image_" + str(objKey[1])
            obj_key = "object_" + str(objKey[2])

            if table_key not in json:
                json[table_key] = {}
            if img_key not in json[table_key]:
                json[table_key][img_key] = {}
            json[table_key][img_key][obj_key] = {}
            json[table_key][img_key][obj_key]['class'] = label
            json[table_key][img_key]['images'] = {}

            paths = db.GetFullChannelPathsForImage(objKey)
            for i,color in enumerate(image_channel_colors):
                json[table_key][img_key]['images'][color] = baseurl + paths[i]

    return json



# each object is nested in its own JSON Object
def calculateTrainingSetJSON(base64=False):

    p = settings['p']
    dm = settings['dm']
    db = settings['db']
    classifier = settings['classifier']

    json_array = [] # Array storing dicts of objects 
    baseurl = p.image_url_prepend
    if baseurl == None:
        baseurl = ''
    image_channel_colors = p.image_channel_colors

    for label,objKey in classifier.trainingSet.entries:
        
        json = {}
        if p.table_id == None:
            json['image'] = objKey[0]
            json['object'] = objKey[1]
        else:
            json['table'] = objKey[0]
            json['image'] = objKey[1]
            json['object'] = objKey[2]

        json['class'] = label
        paths = db.GetFullChannelPathsForImage(objKey)
        for i,color in enumerate(image_channel_colors):
            json[color] = baseurl + paths[i]

        if base64:
            from cStringIO import StringIO
            import base64
            # Convert to Base64
            output = StringIO()
            tile = imagetools.FetchTile(objKey)
            #tile = imagetools.FetchImage(objKey)
            im = imagetools.MergeChannels(tile,p.image_channel_colors)
            im = imagetools.npToPIL(im)
            im.save(output, format='JPEG')
            im_data = output.getvalue()
            data_url = 'data:image/jpg;base64,' + base64.b64encode(im_data)
            json['base64'] = data_url

        json_array.append(json)


    return json_array

# each object is nested in its own JSON Object
def calculateAllJSON(objKeys, base64=True):

    p = settings['p']
    dm = settings['dm']
    db = settings['db']
    classifier = settings['classifier']

    json_array = [] # Array storing dicts of objects 
    baseurl = p.image_url_prepend
    if baseurl == None:
        baseurl = ''
    image_channel_colors = p.image_channel_colors

    for objKey in objKeys:
        
        json = {}
        if p.table_id == None:
            json['image'] = objKey[0]
            json['object'] = objKey[1]
        else:
            json['table'] = objKey[0]
            json['image'] = objKey[1]
            json['object'] = objKey[2]

        paths = db.GetFullChannelPathsForImage(objKey)
        for i,color in enumerate(image_channel_colors):
            json[color] = baseurl + paths[i]

        if base64:
            from cStringIO import StringIO
            import base64
            # Convert to Base64
            output = StringIO()
            tile = imagetools.FetchTile(objKey)
            #tile = imagetools.FetchImage(objKey)
            im = imagetools.MergeChannels(tile,p.image_channel_colors)
            im = imagetools.npToPIL(im)
            im.save(output, format='JPEG')
            im_data = output.getvalue()
            data_url = 'data:image/jpg;base64,' + base64.b64encode(im_data)
            json['base64'] = data_url

        json_array.append(json)

    # Save as local file
    import json
    f = open('23classes.json', 'w')
    json_string = json.dumps(json_array)
    f.write(json_string)
    f.close()

    return json_array


class TrainingSet(Resource):
    def get(self):

        label_array = classifier.trainingSet.label_array.tolist() # (array of class assignments)
        labels = classifier.trainingSet.labels # (class labels)
        colnames = classifier.trainingSet.colnames # (all column names)
        values = classifier.trainingSet.values.tolist() # (training values)
        entries = classifier.trainingSet.entries # (label, obKey)

        return colnames + values[1] # Return col names and values for visualisation purposes

# Get all the cached images from the trainingSet 
class getImagePaths(Resource):
    def get(self):

        p = settings['p']
        dm = settings['dm']
        db = settings['db']
        classifier = settings['classifier']

        # Quickly fetch the pics
        if cached_json['base64'] == False:
            cached_json['json'] = calculateTrainingSetJSON();

        return cached_json['json'], 201, {'Access-Control-Allow-Origin': '*'}

class getBase64(Resource):
    def get(self):
        if cached_json['base64'] == False:
            # Start the virtual machine
            javabridge.start_vm(class_path=bioformats.JARS, run_headless=True)
            javabridge.attach()
            javabridge.activate_awt()

            # Calculate the Training DataSet and store it
            cached_json['json'] = calculateTrainingSetJSON(base64=True)
            cached_json['base64'] = True
        
        return cached_json['json']

         
class getAll(Resource):
    def get(self):
        total = dm.get_total_object_count()
        objKeys = dm.GetRandomObjects(total)

        # Start the virtual machine
        javabridge.start_vm(class_path=bioformats.JARS, run_headless=True)
        javabridge.attach()
        javabridge.activate_awt()

        return calculateAllJSON(objKeys, base64=True)


class helloworld(Resource):
    def get(self):
        return "hello world!", 201, {'Access-Control-Allow-Origin': '*'}


@app.route('/start',methods=['GET'])
def init():
    start()
    return 'starting CPA'

##
## Actually setup the Api resource routing here
##
api.add_resource(helloworld, '/')
#api.add_resource(TrainingSet, '/')
api.add_resource(getImagePaths, '/images')
api.add_resource(getBase64, '/base64')
api.add_resource(getAll, '/all')









#Server Main Function
if __name__ == '__main__':

    #app.debug = True
    #app.run(host='0.0.0.0', port=5000) #Public IP

    start()
    # Start the virtual machine
    javabridge.start_vm(class_path=bioformats.JARS, run_headless=True)
    javabridge.attach()
    javabridge.activate_awt()

    # Calculate the Training DataSet and store it
    calculateTrainingSetJSON(base64=True)





