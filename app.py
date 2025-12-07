import os
from flask import Flask, jsonify, url_for, redirect, render_template_string, Response
from celery.result import AsyncResult

from celery_utils import celery_init_app


app = Flask(__name__)

# --- Celery Configuration ---
app.config.from_mapping(
    CELERY=dict(
        broker_url="redis://127.0.0.1:6379/0",
        result_backend="redis://127.0.0.1:6379/1",
        task_ignore_result=False,
    ),
)
app.config["SECRET_KEY"] = "very-secret-key"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize Celery with our Flask app
celery_app = celery_init_app(app)
celery_app.conf.update(app.config["CELERY"]) # Explicitly update Celery config

import redis
import tasks

redis_client = redis.Redis(host='127.0.0.1', port=6379, db=0)

@app.route("/")
def index():
    return render_template_string("""
    <h1>Flask Celery Demo</h1>
    <p> Try triggering some tasks and check the logs</p>
    <ul>
        <li><a href="{{ url_for('add_task') }}">Trigger Add Task</a></li>
        <li><a href="{{ url_for('long_running_task') }}">Trigger Long Running Task</a></li>
        <li><a href="{{ url_for('unreliable_task') }}">Trigger Unreliable Task</a></li>
    </ul>
    """)

@app.route("/add-task")
def add_task():
    task = tasks.add.delay(4, 6)
    return redirect(url_for("check_task",task_id = task.id))

@app.route("/long-running-task")
def long_running_task():
    task = tasks.long_running_task.delay(5)
    return redirect(url_for("check_task",task_id = task.id))

@app.route("/unreliable-task")
def unreliable_task():
    task = tasks.unreliable_task.delay()
    return redirect(url_for("check_task",task_id = task.id))

@app.route("/check-task/<task_id>")
def check_task(task_id):
    task = AsyncResult(task_id)
    
    if task.ready():
        response_data = {
            "task_id": task.id,
            "task_state": task.state,
            "task_result": task.result,
            "ready": True,
        }
    else:
        response_data = {
            "task_id": task.id,
            "task_state": task.state,
            "ready": False,
        }
    return jsonify(response_data)

@app.route("/task-revoked/<task_id>")
def revoke_task(task_id):
    task = AsyncResult(task_id, app = celery_app)
    if not task.ready():
        task.revoke(terminate=True)
        return jsonify({
            "message":f"Task {task_id} revoked successfully"
        })
    return jsonify({"task_id": task_id, "task_state": task.state})


@app.route("/stream")
def stream():
    def generate_events():
        pubsub = redis_client.pubsub()
        pubsub.subscribe("task_updates")

        for message in pubsub.listen():
            if message['type'] == 'message':
                yield f"data: {message['data'].decode('utf-8')}\n\n"
    
    return Response(generate_events(), mimetype='text/event-stream')
    
if __name__ == "__main__":
    app.run(debug=True)