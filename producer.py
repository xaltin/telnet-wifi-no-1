#!/usr/bin/python
import Queue
import time
import threading
 
q=Queue.Queue()
count = 9
mu = threading.Lock()
# muc = threading.Lock()
class producer(threading.Thread):
    def __init__(self,i):
        threading.Thread.__init__(self,name="producer Thread-%d" % i)
    def run(self):
        global q
        global count
        while True:
            if q.qsize() > 12:
                pass
            if mu.acquire():
                count=count+1
                msg=str(count)
                q.put(msg)
                print self.name+' -'+'produces '+msg+'- '+'Queue Size:'+str(q.qsize())
                mu.release()
                     
            time.sleep(3)
 
class consumer(threading.Thread):
    def __init__(self,i):
        threading.Thread.__init__(self,name="consumer Thread-%d" % i)
    def run(self):
        global q
        while True:
            if q.qsize() < 1:
                pass
            if mu.acquire():
                msg=q.get()
                print self.name+' -'+'consumes '+msg+'- '+'Queue Size:'+str(q.qsize())
                mu.release()
            time.sleep(2)
 
 
def test():
    for i in range(10):
        q.put(str(i))
        print 'Init producer  '+str(i)
    for i in range(2):
        p=producer(i)
        p.start()
    for i in range(3):
        c=consumer(i)
        c.start()
 
if __name__ == '__main__':
    test()