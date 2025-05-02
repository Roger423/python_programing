import threading
import time

class MyThread:
    def __init__(self):
        self._stop_thread = False
        self._thread = threading.Thread(target=self._run)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_thread = True
        self._thread.join()

    def _run(self):
        while not self._stop_thread:
            print("Thread running...")
            time.sleep(1)
        print("Thread exiting...")

# Usage
my_thread = MyThread()
my_thread.start()

# Let it run for 3 seconds, then stop
time.sleep(3)
my_thread.stop()
