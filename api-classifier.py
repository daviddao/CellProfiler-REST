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

TODOS = {
    'todo1': {'task': 'build an API'},
    'todo2': {'task': '?????'},
    'todo3': {'task': 'profit!'},
}


def abort_if_todo_doesnt_exist(todo_id):
    if todo_id not in TODOS:
        abort(404, message="Todo {} doesn't exist".format(todo_id))

parser = reqparse.RequestParser()
parser.add_argument('task')


# Init
p = Properties.getInstance()
p.LoadFile('/vagrant/data/5_classes/2010_08_21_Malaria_MartiLab_Test_2011_05_27_DIC+Alexa.properties')
db = dbconnect.DBConnect.getInstance()
dm = DataModel.getInstance()

classifier = Classifier(properties=p) # Create a classifier with p
classifier.LoadTrainingSet('/vagrant/data/5_classes/MyTrainingSet_AllStages_Half.txt')

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
        return classifier.trainingSet.label_array


##
## Actually setup the Api resource routing here
##
api.add_resource(TodoList, '/todos')
api.add_resource(Todo, '/todos/<todo_id>')
api.add_resource(TrainingSet, '/')


#Server Main Function
if __name__ == '__main__':

    app.debug = True
    app.run(host='0.0.0.0', port=5000) #Public IP



