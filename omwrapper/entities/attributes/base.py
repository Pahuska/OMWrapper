from functools import wraps
from typing import Dict, List, Union, Any

from maya.api import OpenMaya as om

from omwrapper.api import apiundo
from omwrapper.api.modifiers.base import add_modifier
from omwrapper.api.modifiers.custom import ProxyModifier
from omwrapper.api.modifiers.maya import DGModifier, DagModifier
from omwrapper.api.utilities import get_plug_value, set_plug_value, name_to_api
from omwrapper.constants import DataType, AttrType
from omwrapper.entities.base import MayaObject, TMayaObjectApi, recycle_mfn
from omwrapper.pytools import Iterator

TInputs = Union[List[om.MPlug, "Attribute",...], om.MPlug, "Attribute", None]
TOutputs = Union[List[TInputs], None]
TConnect = Union["Attribute", str, om.MPlug]

def recycle_mplug(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        inst = args[0]
        mfn = kwargs.get('mplug', None)
        if mfn is None:
            kwargs['mplug'] = inst.apim_plug()
        result = func(*args, **kwargs)
        return result
    return wrapped

TTime = Union[float, int, om.MTime]

def _as_mplug(attribute:TConnect) -> om.MPlug:
    if isinstance(attribute, Attribute):
        return attribute.api_mplug()
    elif isinstance(attribute, om.MPlug):
        return attribute
    elif isinstance(attribute, str):
        obj = name_to_api(attribute)
        if isinstance(obj, om.MPlug):
            return obj
        else:
            raise TypeError(f'{attribute} is not an attribute')
    else:
        raise TypeError(f'The type of {attribute} ({type(attribute)}) is not supported')

class Attribute(MayaObject):
    _mfn_class = om.MFnAttribute
    _mfn_constant = om.MFn.kAttribute

    def __init__(self, **kwargs:TMayaObjectApi):
        super().__init__(**kwargs)
        self._node = kwargs.get('node', None)
        self._parent = kwargs.get('parent', None)
        self._data_type = None
        self._attr_type = None

    # API STUFF
    def api_mfn(self) -> om.MFnBase:
        return self._mfn_class(self.api_mobject())

    def api_mplug(self) -> om.MPlug:
        return self._api_input['MPlug']

    def api_mdagpath(self):
        #ToDo: implement this when DagNode will be available
        ...

    @classmethod
    def get_build_data_from_name(cls, name:str) -> Dict[str, TMayaObjectApi]:
        sel = om.MSelectionList()
        sel.add(name)

        try:
            mplug = sel.getPlug(0)
        except TypeError:
            raise TypeError(f'{name} is not a valid attribute')

        return {'MObjectHandle':om.MObjectHandle(mplug.attribute()), 'MPlug':mplug}

    # IDENTITY
    def name(self, include_node=True, alias=False, full_attr_path=False, long_names=True) -> str:
        plug_name = self.api_mplug().partialName(includeNodeName=include_node, useAlias=alias,
                                               useFullAttributePath=full_attr_path, useLongNames=long_names)
        return plug_name

    @recycle_mfn
    def attr_name(self, long_name:bool=True, include_node:bool=True, mfn:om.MFnAttribute=None) -> str:
        if long_name:
            name = mfn.name
        else:
            name = mfn.shortName
        if include_node:
            return f'{self.node().name()}.{name}'

    def node(self) -> MayaObject:
        if self._node is None:
            handle = om.MObjectHandle(self.api_mplug().node())
            self._node = self._factory(MObjectHandle=handle)
        return self._node

    @recycle_mplug
    def parent(self, mplug:om.MPlug):
        if self._parent is not None:
            return self._parent

        try:
            parent_plug = mplug.parent()
        except TypeError:
            return None
        parent_mobject = parent_plug.attribute()
        return self._factory(MPlug=parent_plug, MObjectHandle=om.MObjectHandle(parent_mobject), node=self.node())

    @recycle_mfn
    def rename(self, name:str, short_name=False, mfn:om.MFnAttribute=None):
        if short_name:
            mfn.shortName = name
        else:
            mfn.name = name

    # TYPE CONSTANTS
    def attr_type(self) -> DataType:
        if self._data_type is None:
            self._data_type = DataType.from_mobject(self.api_mobject())
        return self._data_type

    def data_type(self) -> AttrType:
        if self._attr_type is None:
            self._attr_type = AttrType.from_mobject(self.api_mobject())
        return self._attr_type

    # PARAMETERS
    @recycle_mplug
    def index(self, mplug) -> int:
        """
        if this is a multi attribute, return the index of this particular element
        Args:
            mplug (MPLug, optional): an optional MPlug representing this attribute

        Returns:
            int: the index of this attribute

        """
        return mplug.logicalIndex()

    @recycle_mplug
    def multi_indices(self, mplug:om.MPlug) -> List[int]:
        return mplug.getExistingArrayAttributeIndices()

    @recycle_mplug
    def is_free_to_change(self, mplug:om.MPlug):
        ftc = mplug.isFreeToChange()
        if ftc == om.MPlug.kFreeToChange:
            return 1
        elif ftc == om.MPlug.kNotFreeToChange:
            return 0
        else:  # ftc == om2.MPlug.kChildrenNotFreeToChange
            return -1

    @recycle_mplug
    def is_dynamic(self, mplug: om.MPlug) -> bool:
        return mplug.isDynamic

    @recycle_mfn
    def is_multi(self, mfn: om.MFnAttribute) -> bool:
        return mfn.array

    @recycle_mplug
    def is_keyable(self, mplug:om.MPlug) -> bool:
        return mplug.isKeyable

    @recycle_mplug
    def set_keyable_(self, value, mplug:om.MPlug):
        mplug.isKeyable = value
        if not value:
            mplug.isChannelBox = True
        else:
            mplug.isChannelBox = False

    @recycle_mplug
    def set_keyable(self, value, mplug:om.MPlug):
        old_value = self.is_keyable(mplug=mplug)
        modifier = ProxyModifier(do_func=self.set_keyable_,
                                 do_kwargs={'value':value, 'mplug':mplug},
                                 undo_kwargs={'value':old_value, 'mplug':mplug})
        modifier.doIt()
        apiundo.commit(undo=modifier.undoIt, redo=modifier.doIt)

    @recycle_mplug
    def is_displayable(self, mplug: om.MPlug) -> bool:
        return mplug.isChannelBox

    @recycle_mplug
    def set_displayable_(self, value, mplug: om.MPlug):
        mplug.isChannelBox = value

    @recycle_mplug
    def set_displayable(self, value, mplug: om.MPlug):
        old_value = self.is_displayable(mplug=mplug)
        modifier = ProxyModifier(do_func=self.set_displayable_,
                                 do_kwargs={'value': value, 'mplug': mplug},
                                 undo_kwargs={'value': old_value, 'mplug': mplug})
        modifier.doIt()
        apiundo.commit(undo=modifier.undoIt, redo=modifier.doIt)

    @recycle_mplug
    def is_locked(self, mplug: om.MPlug) -> bool:
        return mplug.isLocked

    @recycle_mplug
    def set_locked_(self, value, mplug: om.MPlug):
        mplug.isLocked = value

    @recycle_mplug
    def set_locked(self, value, mplug: om.MPlug):
        old_value = self.is_locked(mplug=mplug)
        modifier = ProxyModifier(do_func=self.set_locked_,
                                 do_kwargs={'value': value, 'mplug': mplug},
                                 undo_kwargs={'value': old_value, 'mplug': mplug})
        modifier.doIt()
        apiundo.commit(undo=modifier.undoIt, redo=modifier.doIt)

    # INPUTS AND OUTPUTS
    @recycle_mplug
    def is_source(self, mplug: om.MPlug):
        return mplug.isSource

    @recycle_mplug
    def is_destination(self, mplug: om.MPlug):
        return mplug.isDestination

    @recycle_mplug
    def source(self, skip_conversion:bool=True, as_api:bool=False, mplug:om.MPlug=None) -> TInputs:
        if mplug.isArray:
            result = []
            indices = mplug.getExistingArrayAttributeIndices()
            it = Iterator(indices)
            while not it.is_done():
                index = it.current_item()
                plug = mplug.elementByLogicalIndex(index)
                if plug.isDestination:
                    if skip_conversion:
                        src = plug.source()
                    else:
                        src = plug.sourceWithConversion()

                    if as_api:
                        result.append(src)
                    else:
                        result.append(self._factory(src))
                it.next()
            return result #ToDo: what's the problem here ?
        else:
            if not mplug.isDestination:
                return None
            if skip_conversion:
                src = mplug.source()
            else:
                src = mplug.sourceWithConversion()

            if as_api:
                return src
            else:
                return self._factory(src)

    @recycle_mplug
    def destinations(self, skip_conversion:bool=True, as_api:bool=False, mplug:om.MPlug=None) -> TOutputs:

        def plug_array_to_attribute(array) -> List:
            plug_list = []
            array_it = Iterator(array)
            while not array_it.is_done():
                p = array_it.current_item()
                plug_list.append(self._factory(p))
                array_it.next()
            return plug_list

        if mplug.isArray:
            result = []
            indices = mplug.getExistingArrayAttributeIndices()
            it = Iterator(indices)

            while not it.is_done():
                idx = it.current_item()
                p = mplug.elementByLogicalIndex(idx)
                if p.isSource:
                    if skip_conversion:
                        plug_array = p.destinations()
                    else:
                        plug_array = p.destinationsWithConversion()

                    if as_api:
                        result.append(plug_array)
                    else:
                        result.append(plug_array_to_attribute(plug_array))

                it.next()
            return result
        else:
            if not mplug.isSource:
                return None

            if skip_conversion:
                plug_array = mplug.destinations()
            else:
                plug_array = mplug.destinationsWithConversions()

            if as_api:
                return plug_array
            else:
                return plug_array_to_attribute(plug_array)

    def get(self, as_string:bool=False, time:TTime=None, context:om.MDGContext=None) -> Any:
        """
        Retrieves the value of the attribute at a specified time or within a given evaluation context.

        Args:
            as_string (bool, optional): If True, for enum attributes, the value is returned as a string corresponding
                                        to the field name. Defaults to False.
            time (float, int, MTime, optional): The time at which to evaluate the attribute. Can be:
                - A float or int, interpreted as a frame number.
                - An `MTime` object, directly used to create the evaluation context.
                - None, in which case the default context (`MDGContext.kNormal`) is used, unless overridden by `context`.
            context (MDGContext, optional): The evaluation context to use. If provided, this takes precedence over
                                           the `time` parameter. Defaults to None.

        Returns:
            Any: The value of the attribute at the specified time or in the specified context.

        Notes:
            - If `context` is provided, it overrides the `time` parameter for creating the evaluation context.
            - If `time` is provided but not as an `MTime` object, it is converted to one using the current time unit.
            - The value is retrieved using the `get_plug_value` method, which handles the attribute's data type and context.
        """
        if context is not None:
            eval_ctx = context
        elif time is not None:
            if isinstance(time, om.MTime):
                eval_ctx = om.MDGContext(time)
            else:
                eval_ctx = om.MDGContext(om.MTime(time, unit=om.MTime.uiUnit()))
        else:
            eval_ctx = om.MDGContext.kNormal

        value = get_plug_value(plug=self.api_mplug(), as_string=as_string, context=eval_ctx)
        return value

    @recycle_mplug
    def set_(self, value:Any, data_type:DataType=None, mplug:om.MPlug=None):
        """
        Sets the value of the attribute using the specified MPlug.

        This method provides a simpler and direct way to set the value of an attribute without managing undo or
        modifiers. The MPlug argument is optional and will be derived from the instance if not provided.

        Args:
            value (Any): The value to set on the attribute.
            data_type (DataType, optional): The type of the data being set. If not provided, it will be inferred
                                            based on the plug's attribute.
            mplug (MPlug, optional): The MPlug representing the attribute. If not provided, it defaults to the
                                     plug derived from the instance.

        Notes:
            - This method uses `set_plug_value` for setting the plug value.
            - No undo functionality or modifiers are applied.
        """
        set_plug_value(plug=mplug, value=value, data_type=data_type)

    @recycle_mplug
    @add_modifier(DGModifier, undo=True)
    def set(self, value:Any, data_type:DataType=None, mplug:om.MPlug=None, _modifier:Union[DGModifier, DagModifier]=None):
        """
        Sets the value of the attribute with undo and modifier management.

        This method allows for modifying the attribute value while integrating Maya's undo/redo functionality.
        If a modifier is not provided, one will be instantiated and managed internally.
        If one is provided though, executing the doIt function will be the user's responsibility.

        Args:
            value (Any): The value to set on the attribute.
            data_type (DataType, optional): The type of the data being set. If not provided, it will be inferred
                                            based on the plug's attribute.
            mplug (MPlug, optional): The MPlug representing the attribute. If not provided, it defaults to the
                                        plug derived from the instance.
            _modifier (Union[DGModifier, DagModifier], optional): An optional modifier to manage the operation.
                                                                  If not provided, a `DGModifier` is created.

        Notes:
            - This method uses `_modifier.set_plug_value` to perform the operation.
            - The `add_modifier` decorator ensures undo/redo functionality is managed seamlessly.
            - The `recycle_mplug` decorator ensures the `mplug` argument is initialized if not provided.
        """
        _modifier.set_plug_value(plug=mplug, value=value, data_type=data_type)

    @recycle_mplug
    @add_modifier(DGModifier, undo=True)
    def connect(self, destination:TConnect, force:bool=False, next_available:bool=False,
                mplug:om.MPlug=None, _modifier:DGModifier=None):
        """
        Connects the source attribute (represented by the provided or default MPlug)
        to a destination attribute.

        This method converts the 'destination' parameter into an MPlug using the helper function `_as_mplug` and
        establishes a connection using the provided DGModifier.

        Args:
            destination (Attribute, str, MPlug): The destination attribute to connect to.
            force (bool, optional): If True, forces the connection even if the destination already has a connection.
                Defaults to False.
            next_available (bool, optional): If True, connects to the next available index in an array attribute.
                Defaults to False.
            mplug (MPlug, optional): The optional MPlug representing this attribute. If not provided, it will be fetched
                automatically using the api_mplug method
            _modifier (DGModifier, optional): The modifier used to queue and execute the connection. defaults to a
                DGModifier is none is provided

        Notes:
            - The method uses `_modifier.connect_` to perform the actual connection,
              after converting the destination via `_as_mplug`.

        Returns:
            None
        """

        if mplug.isArray and mplug.attribute().hasFn(om.MFn.kTypedAttribute) and not mplug.isDynamic:
            mplug = mplug.elementByLogicalIndex(0)

        #FixMe: we might need to put this directly in the api_mplug method. What's gonna happen if I try to "get" an
        # attribute like worldMatrix ?

        _modifier.connect_(s_plug=mplug, d_plug=_as_mplug(destination), force=force, next_available=next_available)

    @recycle_mplug
    @add_modifier(DGModifier, undo=True)
    def disconnect(self, *args:TConnect, mplug:om.MPlug=None, _modifier:DGModifier=None):
        """
        Disconnects one or more attributes from this attribute.

        The source objects are first converted to MPlugs using the helper function `_as_mplug`.

        Args:
            *args (TConnect): A variable number of source attributes to disconnect. Each source can be given as an
                Attribute, a string identifier, or an MPlug.
            mplug (MPlug, optional): The optional MPlug representing this attribute. If not provided, it will be fetched
                automatically using the api_mplug method
            _modifier (DGModifier, optional): The modifier used to queue and execute the connection. defaults to a
                DGModifier is none is provided

        Returns:
            None
        """

        plugs = [_as_mplug(obj) for obj in args]
        plugs.insert(0, mplug)
        _modifier.disconnect_(*args)