import threading
import Queue


class CountingQueue(Queue.Queue):
    def __init__(self, maxsize=0):
        # Queue.Queue.__init__(**locals())
        Queue.Queue.__init__(self, maxsize)
        self.__mycount = 0
        self.__total = 0

    def get(self):
        ret = Queue.Queue.get(self)
        self.__mycount += 1
        return ret

    def put(self, i):
        Queue.Queue.put(self, i)
        self.__total += 1

    def get_count(self):
        return self.__mycount

    def get_total(self):
        return self.__total

    def get_progress_desc(self):
        queue = self
        percent = queue.get_count() * 100 / float(queue.get_total())
        return str(queue.get_count()) + "/" + str(queue.get_total()) + " (" + str(percent)[:5] + "%)"


def createTrheadedQueue(target, args, elements):
    WORKERS = min(4, len(elements))
    q = CountingQueue()
    # Start multi-thread. One thread for each worker, all use same queue.
    threads = []
    newargs = (q,) + args
    for i in range(WORKERS):
        import inspect
        if inspect.isclass(target):
            worker = target(*newargs)
        else:
            worker = threading.Thread(target=target, args=newargs)
        worker.setDaemon(True)
        worker.start()
        threads.append(worker)

    # Enqueue all movies in queue
    for i in elements:
        q.put(i)

    print("All elements pushed to queue!")

    for i in range(WORKERS):
        q.put(None)  # add end-of-queue markers

    # Wait threads and workers to finish
    q.join()
