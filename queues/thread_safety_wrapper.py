from contextlib import contextmanager
import threading

class Empty(Exception):
    """ raised when attempting to dequeue from an empty container (i.e. count can't be 
    acquired in ThreadSafetyWrapper.protect_get()). """
    pass

class Full(Exception):
    """ raised when attempting to enqueue into a full container (i.e. space can't be 
    acquired in ThreadSafetyWrapper.protect_put()). """
    pass

""" ensure that enqueue/dequeue are atomic (occur without any intermediate states visible 
to other threads), protecting them against race conditions (multiple threads accessing 
shared data concurrently). """
class ThreadSafetyWrapper:
    def __init__(self, maxsize=None):
        """ threading.Semaphore() implements a semaphore. This synchronisation primitive 
        (mechanism to coordinate the execution of multiple threads in a concurrent system) 
        manages an atomic counter representing the number of release() - acquire() calls, 
        plus an initial value. acquire() blocks if necessary until it can return without 
        making the counter negative. """
        self.count = threading.Semaphore(0)
        """ self.count/space manages the number items/available space. """
        self.space = threading.Semaphore(maxsize) if maxsize else None
        """ threading.Lock() implements a primitive lock object; once a thread has acquired it, 
        subsequent attempts to acquire it block, until it's released; any thread may release it. """
        self.mutex = threading.Lock()

    """ contextlib.contextmanager is a decorator (function that returns another function 
    via a transformative @wrapper) that defines a factory function for with statements 
    without __enter__() and __exit__(). If block is True, the thread blocks until it 
    can proceed with the operation. If it's False, the thread immediately returns 
    if the operation can't be performed. """
    @contextmanager
    def protect_put(self, block):
        """ threading.Semaphore.acquire() acquires a semaphore. When blocking=True, if 
        the counter > 0 on entry,decrement it by 1 and return True immediately. If it's 
        0 on entry, block until awoken by a call to release(). Once awoken (and the counter > 0), 
        decrement the counter by 1 and return True. When blocking=False, if a call without an 
        argument would block, return False immediately. Otherwise, do the same thing as when 
        called without arguments, and return True. """
        if self.space and not self.space.acquire(block): 
            raise Full
        yield
        """ threading.Semaphore.release(n=1) releases a semaphore, incrementing the counter 
        by n. When it was 0 on entry and other threads are waiting for it to become > zero again, 
        wake up n of those threads. """
        self.count.release()

    @contextmanager
    def protect_get(self, block):
        if not self.count.acquire(block): 
            raise Empty
        yield
        if self.space: 
            self.space.release()
