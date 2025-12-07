# Project Role: Tutor
**Note:** I will be acting as a tutor to the user, explaining concepts and guiding the implementation rather than performing all actions autonomously. The user intends to learn from this process.

# Project Analysis: Flask Hybrid (Celery + SSE)

## Project Overview
This project combines **Celery** (for heavy background processing) with **Server-Sent Events (SSE)** (for real-time frontend updates), served via **Gunicorn** and **Gevent**.

**Goal:**
1.  User triggers a task (e.g., `/trigger`).
2.  Flask sends task to Celery Worker.
3.  Flask returns immediately.
4.  User's browser listens to `/stream`.
5.  Celery Worker performs task.
6.  **New:** Celery Worker *publishes* "I'm done" message to Redis Pub/Sub.
7.  Flask (listening to Redis) pushes that event to the Browser via SSE.
8.  Browser updates UI instantly without refreshing.

## Architecture Components

*   **Flask:** The web server.
*   **Celery:** The background worker.
*   **Redis:**
    *   **As Broker:** Queues tasks for Celery.
    *   **As Pub/Sub:** Broadcasting events from Worker -> Flask.
*   **Gunicorn + Gevent:** The WSGI server.
    *   *Why Gevent?* Standard Flask cannot handle many persistent SSE connections (it runs out of threads). Gevent uses "greenlets" (super lightweight threads) to hold thousands of connections open efficiently.
    *   *Why Gunicorn?* To run multiple processes (workers) for stability and performance.

## Roadmap (Next Steps)

1.  **Install Dependencies:**
    *   [x] `uv add gunicorn gevent redis` (Completed).

2.  **Update `app.py`:**
    *   Add a Redis client connection.
    *   Create a `/stream` route using a generator function.
    *   Update `celery_init_app` or task logic to *publish* to Redis upon completion.

3.  **Update `tasks.py`:**
    *   Modify tasks to publish messages to a Redis channel (e.g., `task_updates`) instead of just returning values.

4.  **Frontend (in `app.py`):**
    *   Update the HTML/JS to use `new EventSource('/stream')` instead of the polling logic.

5.  **Run with Gunicorn:**
    *   The command to run will change from `flask run` to `gunicorn -k gevent -w 4 -b :5000 app:app`.
