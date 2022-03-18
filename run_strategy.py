import sys
import time

def record_loop(queue):
    data = queue.get()
    #while True:
    print("looping")
    data.append(["24/02/2022 9:33PM", "TSLA", "SHORT"])
    print(data)
    sys.stdout.flush()
    time.sleep(1)
    queue.put(data)