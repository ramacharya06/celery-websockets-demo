import time
import random
import time
import random
from celery import shared_task

@shared_task
def add(x,y):
    print(f"Adding {x} + {y}")
    time.sleep(1)
    result = x + y
    print(f"Result: {result}")
    return result

@shared_task
def long_running_task(duration):
    print("Long running task started")
    time.sleep(duration)
    print("Long running task finished")
    return f"Long running task completed after {duration} seconds"

@shared_task(bind = True, default_retry_delay = 5, max_retries = 1)
def unreliable_task(self):
    attempt = self.request.retries + 1
    print(f"Attempt {attempt} of unreliable task ...")
    if random.random() < 1 :
        print(f"Unreliable task failed on attempt {attempt}, retrying...")
        raise self.retry(exc=ValueError("Simulated failure"))

    print(f"Unreliable task succeeded on attempt {attempt}")
    return f"Unreliable task completed on attempt {attempt}"
    
    