from flask import Flask, request, jsonify, render_template
from celery import Celery

flask_app = Flask(__name__)

# Configure Celery
flask_app.config['CELERY_BROKER_URL'] = 'pyamqp://guest@localhost//'
flask_app.config['CELERY_RESULT_BACKEND'] = 'rpc://'

# Initialize Celery
celery_app = Celery(flask_app.name, broker=flask_app.config['CELERY_BROKER_URL'])
celery_app.conf.update(flask_app.config)

# Define a Celery task
@celery_app.task
def add(x, y):
    import time
    print("wait 5 seconds")
    time.sleep(5)
    return x + y

# Define a Flask route that will call the Celery task
@flask_app.route('/add', methods=['POST'])
def call_add():
    data = request.get_json()
    x = data.get('x')
    y = data.get('y')
    # Call the Celery task
    result = add.delay(x, y)
    # Return a response that includes the Celery task id
    return jsonify({'task_id': result.id}), 202

# Define a Flask route to retrieve the result of a task
@flask_app.route('/result/<task_id>', methods=['GET'])
def get_result(task_id):
    result = celery_app.AsyncResult(task_id)
    if result.ready():
        return jsonify({'result': result.get()})
    else:
        # and let the client poll until the result is ready.
        return jsonify({'status': 'Pending...'})

@flask_app.route('/check_task/<task_id>', methods=['GET'])
def check_task(task_id):
    task = celery_app.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Task is still processing'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'result': task.result
        }
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'status': str(task.info),  
        }
    return jsonify(response)

@flask_app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    flask_app.run(debug=True)

