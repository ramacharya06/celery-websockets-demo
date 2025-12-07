import time
import random
import redis
import json
from celery import shared_task

redis_client = redis.Redis(host='127.0.0.1', port=6379, db=0)

@shared_task(bind = True)
def add(self, x,y):
    print(f"Adding {x} + {y}")
    time.sleep(1)
    result = x + y
    print(f"Result: {result}")

    message = {
        'task_id':self.request.id,
        'status':'SUCCESS',
        'result':result,
        'task_name':'add',
    }
    redis_client.publish('task_updates',json.dumps(message))

    return result

@shared_task(bind=True) 
def long_running_task(self, duration):
    print("Long running task started")
    time.sleep(duration)
    print("Long running task finished")
    result = f"Long running task completed after {duration} seconds"

    
    message = {
        'task_id': self.request.id,
        'status': 'SUCCESS',
        'result': result,
        'task_name': 'long_running_task'
    }
    redis_client.publish('task_updates', json.dumps(message))
    return result

@shared_task(bind=True, default_retry_delay=5, max_retries=1)
def unreliable_task(self):
    attempt = self.request.retries + 1
    task_id = self.request.id
    task_name = 'unreliable_task'

    print(f"Attempt {attempt} of unreliable task ...")
    try:
        if random.random() < 0.5: 
            print(f"Unreliable task failed on attempt {attempt}, retrying...")
            raise self.retry(exc=ValueError("Simulated failure"))

        print(f"Unreliable task succeeded on attempt {attempt}")
        result = f"Unreliable task completed on attempt {attempt}"
        status = 'SUCCESS'
    except Exception as e:
        if self.request.retries >= self.max_retries:
            print(f"Unreliable task failed permanently after {self.max_retries + 1} attempts.")
            result = f"Task failed permanently: {e}"
            status = 'FAILURE'
        else:
           
            raise 

    message = {
        'task_id': task_id,
        'status': status,
        'result': result,
        'task_name': task_name
    }
    redis_client.publish('task_updates', json.dumps(message))
    return result