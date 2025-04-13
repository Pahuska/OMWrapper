from abc import ABC, abstractmethod
from functools import wraps
from typing import Union, Dict, Callable

from maya.api import OpenMaya as om

from omwrapper.entities.factory import PyObject

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
        inst = args[0]
        mfn = kwargs.get('mfn', None)
        if mfn is None:
            kwargs['mfn'] = inst.api_mfn()
        result = func(*args, **kwargs)
        return result
    return wrapped
