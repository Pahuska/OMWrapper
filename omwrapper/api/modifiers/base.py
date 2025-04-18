from abc import ABC, abstractmethod
from functools import wraps
from typing import Union, Callable, Any, Type

from maya.api import OpenMaya as om

from omwrapper.api import apiundo


class AbstractModifier(ABC):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.doIt()

    @abstractmethod
    def doIt(self) -> None:
        ...

    @abstractmethod
    def undoIt(self) -> None:
        ...


TModifier = Union[om.MDGModifier, om.MDagModifier, AbstractModifier]

def add_modifier(_modifier:Type[TModifier], undo:bool=True, post_call:Callable=None) -> Callable:
    """
    A decorator to apply a specific type of modifier to compatible functions
    Args:
        _modifier (AbstractModifier, MDGModifier, MDagModifier): the class of modifier to instantiate
        undo (bool): whether to manage the undo or not

    Returns:
        Callable : the wrapped function

    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args:Any, **kwargs:Any) -> Any:
            # If no modifier was provided, create one.
            if kwargs.get('_modifier', None) is None:
                modifier = _modifier()
                kwargs['_modifier'] = modifier
                result = func(*args, **kwargs)
                modifier.doIt()

                # If undo is True, then pass the newly created modifier into the apiundo.commit function
                if undo:
                    apiundo.commit(modifier.undoIt, modifier.doIt)
                if post_call:
                    post_call()
                return result
            # Else, just execute the function
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator