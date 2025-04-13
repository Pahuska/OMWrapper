from typing import overload, Tuple, Union, Callable, Any

from maya.api import OpenMaya as om

from omwrapper.api.utilities import name_to_api
from omwrapper.constants import ObjectType

class PyObject:
    """
    Singleton Factory class responsible for creating the right subclass of MayaObject
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._registry = {}
        return cls._instance

    def __call__(self, *args, **kwargs) -> Any:
        return self._create(*args, **kwargs)

    def register(self, object_type:ObjectType, cls:Callable):
        self._registry[object_type] = cls

    @overload
    def _create(self, args: str) -> Any:
        """
        Create a new MayaObject instance from an object name
        Args:
            args (str): a string representing the object name
        Returns:
            MayaObject: a MayaObject instance representing the given object
        """
        ...

    @overload
    def _create(self, args: Tuple[om.MDagPath, Union[om.MObject, om.MObjectHandle]]) -> Any:
        """
        Create a new MayaObject instance from a combination of MDagPath and MObject. Used for Components
        Args:
            args (tuple): a tuple with a MDagPath and a MObject or MObjectHandle
        Returns:
            MayaObject: a MayaObject instance representing the given object
        """
        #ToDo: make sure this is actually for Dag nodes. I cant remember. It might actually be components
        ...

    @overload
    def _create(self, *args: Union[om.MDagPath, om.MObjectHandle, om.MObject, om.MPlug]) -> Any:
        """
        Create a new MayaObject instance from various API objects. This method is just here for convenience, allowing
        the user to use it with non-keyword arguments. Eventually all the arguments passed will be identified and the
        PyObject will be called again with keyword arguments.
        Args:
            *args (MDagPath | MObject | MObjectHandle | MPlug): one or more API objects
        Returns:
            MayaObject: a MayaObject instance representing the given object
        """
        ...

    @overload
    def _create(self, MPlug: om.MPlug = None,
                MObjectHandle: om.MObjectHandle = None,
                MObject: om.MObject = None,
                MDagPath: om.MDagPath = None,
                ) -> Any:
        """
        Create a new MayaObject instance from various API objects. Different objects are needed depending on the type of
        the object.
        Args:
            MPlug (MPlug): an MPlug Instance representing an attribute
            MObjectHandle (MObjectHandle): an MObjectHandle instance representing a maya object
            MObject (MObject): an MObject instance representing a maya object. If the object is a dag node and no
            MDagPath is provided, then it will look for the first instance of this node
            MDagPath (MDagPath): an MDagPath  instance representing a dag node
        Returns:
            MayaObject: a MayaObject instance representing the given object
        """
        ...

    def _create(self, *args, **kwargs) -> Any:
        """
        Create a new MayaObject from various type of inputs. Check the overloaded methods for more details
        Returns:
             MayaObject: a MayaObject instance representing the given object
        """
        assert len(args) <= 1, 'PyObject does not take more than 1 non-keyword parameter'

        #ToDo : make a method somewhere that would convert args into kwargs so that we can use that to jump straight to
        # case 4 and avoid the situation where we get a string, process it, pass it back into PyObject, process it again
        # and pass it a third time into PyObject
        if len(args) == 1:
            # CASE 1 : a string was provided, and we are looking for a corresponding API object. We then call PyObject
            # again with whatever we found
            arg = args[0]
            if isinstance(arg, str):
                return self._create(name_to_api(arg), **kwargs)
            else:
                dic = {}
                if isinstance(arg, tuple):
                    # CASE 2 : a tuple was provided, and it contains an MDagPath and an MObject or MObjectHandle
                    # we put them in a dict and pass it as kwargs back into PyObject
                    assert len(arg) == 2, 'PyObjectFactory : Invalid tuple length'
                    assert isinstance(arg[0], om.MDagPath) and isinstance(arg[1], (om.MObject, om.MObjectHandle)), \
                        'PyObject : Invalid tuple composition'

                    for obj in arg:
                        dic[obj.__class__.__name__] = obj
                else:
                    # CASE 3 : one or more API object were provided, such as MPlug, MDagPath, MObject...
                    # we identify them and pass them back as kwargs into PyObject
                    assert isinstance(arg, (om.MDagPath, om.MObjectHandle, om.MObject, om.MPlug)), \
                        f'PyObject : Invalid param type {type(arg)}'

                    dic[arg.__class__.__name__] = arg
                dic.update(kwargs)
                return self._create(**dic)
        else:
            # CASE 4 : keywords args for any of the supported Maya API objects were provided, and we are going to treat
            # them in a specific order to get the right MayaObject out of it. Eventually, all the previous cases end up
            # being treated here.
            assert any(k in ('MDagPath', 'MObject', 'MObjectHandle', 'MPlug') for k in kwargs), \
                'PyObject keyword parameter needs at least one of : (MDagPath, MObject, MObjectHandle, MPlug)'

            if 'MPlug' in kwargs:
                # CASE 4A : an MPlug was provided. Let's get an MObject out of it
                mobj = kwargs['MPlug'].attribute()
            elif 'MObjectHandle' in kwargs:
                # CASE 4B : an MObjectHandle was provided. Let's get an MObject out of it
                mobj = kwargs['MObjectHandle'].object()
            else:
                # CASE 4C : none of the above were provided
                mobj = kwargs.pop('MObject', None)
                if mobj is not None:
                    if 'MDagPath' not in kwargs and mobj.hasFn(om.MFn.kDagNode):
                        kwargs['MDagPath'] = om.MDagPath.getAPathTo(mobj)
                else:
                    mobj = kwargs['MDagPath'].node()

            if 'MObjectHandle' not in kwargs:
                kwargs['MObjectHandle'] = om.MObjectHandle(mobj)

            _class = self.class_from_api_object(mobj)
            # ToDo: finish to implement this ^, but we need some work done on the MayaObject subclasses first
            assert 'MObjectHandle' in kwargs, 'DEBUG : MObjectHandle missing from kwargs ' \
                                              '\nclass:<{}>\nkwargs:{}'.format(_class, kwargs)

            return _class(**kwargs)

    def class_from_api_object(self, api_obj:Union[om.MDagPath, om.MObject]) -> Callable:
        """
        Get the proper class from the registry for an API object. We first narrow it down by figuring out the global
        type. Is it a DependencyNode ? An Attribute ? etc... then try to get more specific. If we can't, we just fall
        back to the global type

        Args:
            api_obj (MDagPath, MObject): the api object to get the class for

        Returns:
            Callable: the input from the registry that matches this api object

        """
        for mfn in ObjectType.iter_mfn():
            if api_obj.hasFn(mfn):
                global_type = ObjectType.from_mfn(mfn)
                break
        else:
            raise TypeError(f'Unrecognized api type : {api_obj.apiType}')

        cls = self._registry.get(global_type, None)
        if cls is None:
            raise NotImplementedError(f'{global_type} is not yet implemented')

        return cls





