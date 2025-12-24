# Flask Celery SSE Demo

This project demonstrates a real-time asynchronous task queue system using **Flask**, **Celery**, **Redis**, and **Server-Sent Events (SSE)**.

It shows how to offload long-running tasks to a background worker (Celery) and push real-time updates to the frontend (using SSE) when tasks complete or update their status, without requiring the client to poll the server.

## Architecture

1.  **Flask**: Serves the web application and handles HTTP requests.
2.  **Celery**: Executes tasks in the background (e.g., heavy computations, API calls).
3.  **Redis**:
    *   Acts as the **Message Broker** for Celery (queuing tasks).
    *   Acts as a **Pub/Sub** system to broadcast task updates from Celery workers to the Flask server.
4.  **SSE (Server-Sent Events)**: The Flask server pushes updates to the client browser in real-time.

## Prerequisites

*   Python 3.x
*   Redis Server

## Installation

1.  Install dependencies (using `uv` or `pip`):
    ```bash
    # using uv
    uv sync
    
    # OR using pip
    pip install flask celery[redis] redis gunicorn gevent
    ```

## Running the Application

You need to run three separate components (terminals):

### 1. Start Redis Server
Ensure Redis is running on the default port (6379).
```bash
redis-server
```

### 2. Start Celery Worker
This processes the background tasks.
```bash
celery -A app.celery_app worker --loglevel=info
```

### 3. Start the Web Server
Use Gunicorn with Gevent worker class to support asynchronous SSE connections efficiently.
```bash
gunicorn -k gevent -w 4 -b :5000 app:app
```
*Access the application at http://localhost:5000*

## Usage

1.  Open the application in your browser.
2.  Click on the links to trigger different types of tasks:
    *   **Add Task:** A simple addition task.
    *   **Long Running Task:** Simulates a 5-second delay.
    *   **Unreliable Task:** A task that may fail and retry automatically.
3.  Watch the "Task Updates" section. You will see real-time notifications appear as the tasks are processed and completed by the Celery worker.

## Project Structure

*   `app.py`: Main Flask application, routes, and SSE generator.
*   `tasks.py`: Celery task definitions.
*   `celery_utils.py`: Helper to initialize Celery with Flask context.
