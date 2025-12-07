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
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Flask Celery SSE Demo</title>
        <style>
            body { font-family: sans-serif; margin: 20px; }
            .task-list { border: 1px solid #ccc; padding: 10px; min-height: 100px; max-height: 400px; overflow-y: scroll; background-color: #f9f9f9; }
            .task-item { padding: 5px 0; border-bottom: 1px dotted #eee; }
            .task-item:last-child { border-bottom: none; }
            .status-SUCCESS { color: green; font-weight: bold; }
            .status-FAILURE { color: red; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>Flask Celery SSE Demo</h1>
        <p>Trigger tasks and watch updates appear in real-time below!</p>
        <ul>
            <li><a href="{{ url_for('add_task') }}">Trigger Add Task (4 + 6)</a></li>
            <li><a href="{{ url_for('long_running_task') }}">Trigger Long Running Task (5s)</a></li>
            <li><a href="{{ url_for('unreliable_task') }}">Trigger Unreliable Task (may fail/retry)</a></li>
        </ul>

        <h2>Task Updates (Real-time via SSE)</h2>
        <div id="taskUpdates" class="task-list">
            <p>Waiting for task updates...</p>
        </div>

        <script>
            const eventSource = new EventSource('/stream');
            const taskUpdatesDiv = document.getElementById('taskUpdates');

            eventSource.onmessage = function(event) {
                const data = JSON.parse(event.data);
                const p = document.createElement('p');
                p.className = 'task-item';
                let statusClass = '';
                if (data.status) {
                    statusClass = 'status-' + data.status;
                }
                p.innerHTML = `<strong>Task ID:</strong> ${data.task_id} <br> 
                               <strong>Task Name:</strong> ${data.task_name} <br>
                               <strong>Status:</strong> <span class="${statusClass}">${data.status || 'UNKNOWN'}</span> <br>
                               <strong>Result:</strong> ${data.result || 'N/A'}`;
                
                if (taskUpdatesDiv.firstChild && taskUpdatesDiv.firstChild.tagName === 'P' && taskUpdatesDiv.firstChild.textContent === 'Waiting for task updates...') {
                    taskUpdatesDiv.removeChild(taskUpdatesDiv.firstChild);
                }
                taskUpdatesDiv.prepend(p);
            };

            eventSource.onerror = function(err) {
                console.error("EventSource failed:", err);
                taskUpdatesDiv.innerHTML += '<p style="color: red;">Connection to task updates lost. Try refreshing.</p>';
                eventSource.close();
            };
        </script>
    </body>
    </html>
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