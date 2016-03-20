import datetime
import threading
import Queue


def progress_format(total, current):
    percent = 100 * current / float(total)
    return '{}/{}={}%'.format(current, total, str(percent)[:5])
    pass


class Eta:
    def __get_now(self):
        return datetime.datetime.now()

    def __init__(self, total=None):
        self._total = total
        self._init_time = self.__get_now()
        pass

    def set_current(self, current):
        self._current = current

    def set_total(self, total):
        self._total = total

    def format(self):
        elapsed = (self.__get_now() - self._init_time)
        tot_time = elapsed * self._total / self._current
        pend_time = tot_time - elapsed
        return '{} {}/{}'.format(progress_format(current=self._current, total=self._total), pend_time, tot_time)


class CountingQueue(Queue.Queue):
    def __init__(self, maxsize=0):
        # Queue.Queue.__init__(**locals())
        Queue.Queue.__init__(self, maxsize)
        self.__mycount = 0
        self.__total = 0
        self.__eta = Eta()

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
        self.__eta.set_total(self.__total)
        self.__eta.set_current(self.__mycount)
        formatted = self.__eta.format()
        return formatted


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
