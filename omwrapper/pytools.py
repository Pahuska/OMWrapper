import time
from collections import OrderedDict
from functools import wraps
from typing import List, Any


class Iterator:
    """
    A custom iterator class that iterates over a collection of data.

    Attributes:
        data (List[Any]): The collection of data to be iterated over.
        n (int): The current index in the iteration.

    Methods:
        __len__(): Returns the length of the collection.
        __iter__(): Initializes and returns the iterator object.
        __next__(): Returns the next item in the iteration. Raises StopIteration if the end is reached.
        next(): An alias for __next__().
        is_done(): Checks if the iteration is complete.
        current_item(): Returns the current item in the iteration. Raises IndexError if out of bounds.
        current_index(): Returns the current index in the iteration.
    """

    def __init__(self, data: List[Any]) -> None:
        """
        Initializes the iterator with the given data.

        Args:
            data (List[Any]): The collection of data to iterate over.
        """
        self.data: List[Any] = data
        self.n: int = 0

    def __len__(self) -> int:
        """
        Returns the length of the collection.

        Returns:
            int: The number of items in the collection.
        """
        return len(self.data)

    def __iter__(self) -> 'Iterator':
        """
        Initializes and returns the iterator object.

        Returns:
            Iterator: The initialized iterator object.
        """
        self.n = 0
        return self

    def __next__(self) -> Any:
        """
        Returns the next item in the iteration.

        Returns:
            Any: The next item in the collection.

        Raises:
            StopIteration: If the iteration has reached the end of the collection.
        """
        if self.n < len(self.data):
            result = self.data[self.n]
            self.n += 1
            return result
        else:
            raise StopIteration

    def next(self) -> Any:
        """
        Alias for __next__().

        Returns:
            Any: The next item in the collection.

        Raises:
            StopIteration: If the iteration has reached the end of the collection.
        """
        return self.__next__()

    def is_done(self) -> bool:
        """
        Checks if the iteration is complete.

        Returns:
            bool: True if the iteration is complete, False otherwise.
        """
        return self.n >= len(self.data)

    def current_item(self) -> Any:
        """
        Returns the current item in the iteration.

        Returns:
            Any: The current item in the collection.

        Raises:
            IndexError: If the current index is out of bounds.
        """
        if self.n < len(self.data):
            return self.data[self.n]
        else:
            raise IndexError("Iterator out of range")

    def current_index(self) -> int:
        """
        Returns the current index in the iteration.

        Returns:
            int: The current index in the collection.
        """
        return self.n


class Signal:
    def __init__(self):
        self.listeners = []

    def connect(self, callback):
        """Connect a listener to the signal."""
        self.listeners.append(callback)

    def emit(self, *args, **kwargs):
        """Emit the signal to all connected listeners."""
        for listener in self.listeners:
            listener(*args, **kwargs)

def timeit(name:str='timer', log:bool=False, verbose:bool=True):
    def wrapper(func):
        @wraps(func)
        def timed(*args, **kwargs):
            with Timer(name=name, log=log, verbose=verbose):
                result = func(*args, **kwargs)
            return result
        return timed
    return wrapper

class Timer:
    result_dic = OrderedDict()

    def __init__(self, name:str='timer', log:bool=False, verbose:bool=True):
        self.start = None
        self.end = None
        self.verbose = verbose
        self.name = name
        self.log = log
        self.interval = None

    def __enter__(self):
        self.start = time.time()
        return self

    def time_it(self):
        self.end = time.time()
        self.interval = self.end - self.start

        if self.log is not None:
            if self.name not in self.result_dic:
                self.result_dic[self.name] = 0.0
            self.result_dic[self.name] += self.interval

        if self.verbose:
            print(self.name, ':', self.interval)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.time_it()

    @classmethod
    def print_dic(cls, clear=False):
        for k, v in cls.result_dic.items():
            print('{} : {}'.format(k, v))
        if clear:
            cls.clear_dic()

    @classmethod
    def clear_dic(cls, **kwargs):
        if len(kwargs):
            for k, v in kwargs.items():
                if k in cls.result_dic and v:
                    del cls.result_dic[k]
        else:
            cls.result_dic = OrderedDict()

def get_by_index(obj, index):
    if index < 0 < len(obj):
        raise IndexError("Index out of bounds.")
    for i, value in enumerate(obj):
        if i == index:
            return value