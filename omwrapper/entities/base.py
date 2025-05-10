import inspect
from abc import ABC, abstractmethod
from functools import wraps
from typing import Union, Dict, Callable, Any

from maya.api import OpenMaya as om
import maya.OpenMaya as om1

from omwrapper.api import apiundo
from omwrapper.api.modifiers.custom import ProxyModifier
from omwrapper.api.utilities import unique_object_exists
from omwrapper.entities.factory import PyObject
from omwrapper.pytools import get_by_index

TMayaObjectApi = Union[om.MObject, om.MObjectHandle, om.MPlug, om.MDagPath]

class MayaObject(ABC):
    """
    Abstract base class responsible for representing any object in maya, nodes, attributes...
    """
    _mfn_class = om.MFnBase
    _mfn_constant = om.MFn.kInvalid
    _factory = PyObject()

    @abstractmethod
    def __init__(self, **kwargs: TMayaObjectApi):
        self._api_input = kwargs

    def __repr__(self):
        return '{} <{}>'.format(self.name(), self.__class__.__name__)

    def __str__(self):
        name = self.name()
        if unique_object_exists(name):
            return name
        else:
            return self.name(full_dag_path=True)

    def __eq__(self, other):
        if isinstance(other, MayaObject):
            return self.api_mobject() == other.api_mobject()
        else:
            return NotImplemented

    @abstractmethod
    def api_mfn(self) -> om.MFnBase:
        """
        This method provides an instance of the proper function set (_mfn_class) for this object

        Returns:
            MFnBase subclass: an instance of the MFnBase subclass specified in _mfn_class initialized with this object

        """
        ...

    def api_mobject(self) -> om.MObject:
        """
        Fetches the MObject from the Handle found in the _api_input dict

        Returns:
            MObject: the MObject representing this object

        """
        return self._api_input['MObjectHandle'].object()

    def api_mobject_handle(self) -> om.MObjectHandle:
        """
        Fetches the MObject from the Handle found in the _api_input dict

        Returns:
            MObject: the MObject representing this object

        """
        return self._api_input['MObjectHandle']

    def api_object(self) -> Any:
        """
        Get the default api 2.0 object that represent this object.

        Returns:
            Any: return type varies depending on the type of object. Attributes will return an MPlug, while nodes will
             return an MObject and components a tuple made of an MDagPath and an MObject

        """
        return self.api_mobject()

    @abstractmethod
    def name(self, full_dag_path:bool=False) -> str:
        """
        Get the name of the object
        Args:
            full_dag_path (bool):  True will include the full path with the name

        Returns:
            str: the name of the object

        """
        ...

    def _get_selectable_object(self):
        """
        Returns an object that can be added to an MSelectionList

        :rtype: MObject
        """
        return self.api_mobject()

    @classmethod
    @abstractmethod
    def get_build_data_from_name(cls, name:str) -> Dict[str, TMayaObjectApi]:
        """
        Given a name, provides the API objects needed to initialize it in this very class

        Args:
            name (str): the name of the object

        Returns:
            Dict: a dictionary that holds the keyword args expected by the __init__ function

        """
        ...


def recycle_mfn(func:Callable):
    @wraps(func)
    def wrapped(*args, **kwargs):
        signature = inspect.signature(func)
        bound_args = signature.bind(*args, **kwargs)
        bound_args.apply_defaults()
        bound_kwargs = bound_args.arguments

        inst = bound_kwargs['self']
        mfn = bound_kwargs.get('mfn', None)
        if mfn is None:
            bound_kwargs['mfn'] = inst.api_mfn()
        result = func(**bound_kwargs)
        return result
    return wrapped

def undoable_proxy_wrap(get_method, set_method):
    """
    A decorator that helps to wrap non-undoable methods into a ProxyModifier to make them undoable. This is typically
    used for actions that can't be easily made undoable with a classic modifier. The decorator requires a pair of get
    and set methods.
    The process is as follows:
        - get the Signature of the set_method and fill it with the provided args & kwargs
        - get the Signature of the get_method and fill it with the matching kwargs from the previous step
        - get the current value with the get_method
        - copy the OrderedDict from step 1 and update the second param(which is assumed to be the value to set, as the
          first param should be the instance (self))
        - create the ProxyModifier, execute it and register it for undoing

    Args:
        get_method (Callable): the method used to get the current value
        set_method (Callable): the method used to set the new value, and set the old value when undoing
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get the signature of set_method and fill it with the args and kwargs, then convert it to an OrderedDict
            #  so that we have all the kwargs parameters filled

            set_signature = inspect.signature(set_method)
            do_bound_args = set_signature.bind(*args, **kwargs)
            do_bound_args.apply_defaults()
            do_kwargs = do_bound_args.arguments

            # Get the signature of get_method and fill it with the matching kwargs from set_method, then get the current
            #  value so that we can use it for undoing
            get_parameters = inspect.signature(get_method).parameters.keys()
            get_kwargs = {k:v for k, v in do_kwargs.items() if k in get_parameters}
            old_value = get_method(**get_kwargs)

            # get the second parameter of set_method, which is assumed to be the value to set.
            #  note : The first parameter should be the instance (self)
            k = get_by_index(do_kwargs, 1)
            undo_kwargs = do_kwargs.copy()
            undo_kwargs[k] = old_value

            # Create the ProxyModifier and execute it, then register it for undoing
            mod = ProxyModifier(do_func=set_method, do_kwargs=do_kwargs, undo_kwargs=undo_kwargs)
            mod.doIt()
            apiundo.commit(undo=mod.undoIt, redo=mod.doIt)
        return wrapper
    return decorator