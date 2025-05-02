"""
Using a Flag (Recommended):

Use a shared variable (flag) to signal the thread to stop.
Periodically check the flag inside the thread's loop.
"""
import threading
import time

# Shared flag to control thread
stop_thread = False

def my_thread():
    while not stop_thread:
        print("Thread running...")
        time.sleep(1)
    print("Thread exiting...")

# Start the thread
print(f'Start backgroud thread...')
thread = threading.Thread(target=my_thread)
thread.start()

# Let it run for 3 seconds, then stop
print('Wait for 5 seconds...')
st_time = time.time()
while time.time() - st_time < 5:
    time.sleep(1)
    print(f'Backgroud process is alive: {thread.is_alive()}')
print('Stop backgroud thread')
stop_thread = True

# Wait for the thread to finish
thread.join()
print(f'Backgroud process is alive: {thread.is_alive()}')
