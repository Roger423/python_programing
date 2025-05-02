"""
Using threading.Event:
Use a threading.Event object to signal the thread to exit.
"""

import threading
import time

# Create an Event object
stop_event = threading.Event()

def my_thread():
    while not stop_event.is_set():
        print("Thread running...")
        time.sleep(1)
    print("Thread exiting...")

thread = threading.Thread(target=my_thread)
thread.start()

# Let it run for 3 seconds, then stop
time.sleep(3)
stop_event.set()

# Wait for the thread to finish
thread.join()
