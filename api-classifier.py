from classifier_headless import *

# For test purposes
from cpa.properties import Properties
import cpa.dbconnect as dbconnect
from cpa.datamodel import DataModel

# ----------------- Run -------------------

from flask import Flask
from flask_restful import Resource, Api, reqparse

app = Flask(__name__)
api = Api(app)


# Init
p = Properties.getInstance()
#p.LoadFile('/vagrant/data/23_classes/az-dnaonly.properties')
p.LoadFile('/vagrant/data/5_classes/2010_08_21_Malaria_MartiLab_Test_2011_05_27_DIC+Alexa.properties')
#p.LoadFile('/vagrant/data/cpa_example/example.properties')


db = dbconnect.DBConnect.getInstance()
dm = DataModel.getInstance()

classifier = Classifier(properties=p) # Create a classifier with p
#classifier.LoadTrainingSet('/vagrant/data/23_classes/Anne_DNA_66.txt')
classifier.LoadTrainingSet('/vagrant/data/5_classes/MyTrainingSet_AllStages_Half.txt')
#classifier.LoadTrainingSet('/vagrant/data/cpa_example/MyTrainingSet.txt')

# Helper methods

# Structure of JSON which is sorted after table and images
#{ img_key: { images: {image_channel_color: img_path} ,obj_key: {class: label, x: cell_x, y: cell_y}}}
def calculateStructuredJSON():

    json = {}
    baseurl = p.image_url_prepend
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
def calculateTrainingSetJSON():
    json_array = [] # Array storing dicts of objects 
    baseurl = p.image_url_prepend
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

        json_array.append(json)

    return json_array



# Calculate the Training DataSet and store it
json = calculateTrainingSetJSON()

# Todo
# shows a single todo item and lets you delete a todo item
class Todo(Resource):
    def get(self, todo_id):
        abort_if_todo_doesnt_exist(todo_id)
        return TODOS[todo_id]

    def delete(self, todo_id):
        abort_if_todo_doesnt_exist(todo_id)
        del TODOS[todo_id]
        return '', 204

    def put(self, todo_id):
        args = parser.parse_args()
        task = {'task': args['task']}
        TODOS[todo_id] = task
        return task, 201


# TodoList
# shows a list of all todos, and lets you POST to add new tasks
class TodoList(Resource):
    def get(self):
        return TODOS

    def post(self):
        args = parser.parse_args()
        todo_id = int(max(TODOS.keys()).lstrip('todo')) + 1
        todo_id = 'todo%i' % todo_id
        TODOS[todo_id] = {'task': args['task']}
        return TODOS[todo_id], 201

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
        return json, 201, {'Access-Control-Allow-Origin': '*'}

class helloworld(Resource):
    def get(self):
        return "Hello World!", 201, {'Access-Control-Allow-Origin': '*'}
            

##
## Actually setup the Api resource routing here
##
api.add_resource(helloworld, '/')
api.add_resource(TodoList, '/todos')
api.add_resource(Todo, '/todos/<todo_id>')
api.add_resource(TrainingSet, '/')
api.add_resource(getImagePaths, '/images')


#Server Main Function
if __name__ == '__main__':

    app.debug = True
    app.run(host='0.0.0.0', port=5000) #Public IP



