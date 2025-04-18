from dataclasses import dataclass, field
from functools import wraps
from typing import Dict, List, Union, Any, Optional, Iterable, Tuple

from maya.api import OpenMaya as om

from omwrapper.api import apiundo
from omwrapper.api.modifiers.base import add_modifier
from omwrapper.api.modifiers.custom import ProxyModifier
from omwrapper.api.modifiers.maya import DGModifier, DagModifier
from omwrapper.api.utilities import get_plug_value, set_plug_value, name_to_api
from omwrapper.constants import DataType, AttrType
from omwrapper.entities.base import MayaObject, TMayaObjectApi, recycle_mfn
from omwrapper.pytools import Iterator, Signal

TInputs = Union[List[om.MPlug, "Attribute",...], om.MPlug, "Attribute", None]
TOutputs = Union[List[TInputs], None]
TConnect = Union["Attribute", str, om.MPlug]
TDefaultValues = int, float, str, bool, List[int, float]
TEnumField = List[Tuple[str, int]]

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

@dataclass
class AttrData:
    """
    Represents attribute configuration data similar to the flags used in maya.cmds.addAttr.

    Attributes:
        long_name (str): The long name for the attribute.
        short_name (str): The short name for the attribute.
        attr_type (AttrType): The type of attribute.
        data_type (Optional[DataType]): The data type of the attribute's value, if applicable.
        default_value (Optional[int, float, Iterable[int, float]]): The default value for the attribute.
        keyable (bool): Indicates whether the attribute is keyable for animation. Defaults to False.
        readable (bool): Indicates whether the attribute is readable. Defaults to True.
        min (Optional[int, float, Iterable[int, float]]): The minimum allowed value for the attribute.
        max (Optional[int, float, Iterable[int, float]]): The maximum allowed value for the attribute.
        soft_min (Optional[int, float, Iterable[int, float]]): The soft minimum value hint for the attribute.
        soft_max (Optional[int, float, Iterable[int, float]]): The soft maximum value hint for the attribute.
        multi (Optional[bool]): Specifies if the attribute is multi. False by default.
        index_matters (Optional[bool]): For multi-attributes, determines if indexing is significant. Defaults to False.
        enum_names (Optional[str]): A string with names if the attribute is an enum.
            (e.g.: ('blue:green:red', 'one=1:twenty=20:hundred=100'))
        as_filename (Optional[bool]): Indicates whether the attribute should be treated as a filename. Defaults to False.
    """
    # Creation
    long_name: str
    attr_type: Optional[AttrType] = None
    data_type: Optional[DataType] = None
    short_name: Optional[str] = None
    default_value: Optional[TDefaultValues] = None
    # Post Process
    keyable: bool = False
    readable: bool = True
    min: Optional[TDefaultValues] = None
    max: Optional[TDefaultValues] = None
    soft_min: Optional[TDefaultValues] = None
    soft_max: Optional[TDefaultValues] = None
    multi: Optional[bool] = False
    index_matters: Optional[bool] = False
    enum_names: Optional[str] = None
    enum_fields: Optional[TEnumField] = None
    as_filename: Optional[bool] = False
    children_count:int = None
    parent:Union["AttrData", str, None]=None
    # Internal
    create_args: field(init=False, default_factory=list) = None

    def __post_init__(self):
        self._process_data()

    def _process_data(self):
        # If no short name was provided, make it default to the long name
        if self.short_name is None:
            self.short_name = self.long_name

        self.create_args.append(self.long_name, self.short_name)

        # if no AttrType was provided, guess it from the DataType (applicable for UNIT and NUMERIC attribute types)
        if self.attr_type is None:
            self.attr_type = AttrType.from_data_type(self.data_type)
            if self.attr_type == AttrType.INVALID:
                raise TypeError('Invalid attribute type')

        # in the case of a UNIT or NUMERIC attribute, make sure we have a default value
        if self.attr_type in (AttrType.UNIT, AttrType.NUMERIC) and self.data_type not in (
        DataType.COLOR, DataType.FLOAT3):
            if self.default_value is None:
                self.default_value = 0.0

            self.create_args.append(DataType.to_api_type(self.data_type))
            self.create_args.append(self.default_value)

        # Default values for STRING attribute must be an MObject, so we create one using MFnStringData
        if self.attr_type == AttrType.STRING:
            if self.default_value is None:
                self.default_value = om.MObject.kNullObj
            else:
                string_data = om.MFnStringData()
                self.default_value = string_data.create(self.default_value)

            self.create_args.append(om.MFnData.kString)
            self.create_args.append(self.default_value)

        # If the AttrType is ENUM, we need to process the enum_names into enum_fields.
        # Then, if no default value was provided, use the smallest int in the fields
        if self.attr_type == AttrType.ENUM:
            if self.enum_names is not None:
                self.enum_fields = AttrData.enum_str_to_field(self.enum_names)
            else:
                if self.enum_fields is None:
                    raise ValueError('If the AttrType is en ENUM, enum_names or enum_fields is required')

            if self.default_value is None:
                self.default_value = min(self.enum_fields, key=lambda x: x[1])[1]

        if self.attr_type == AttrType.COMPOUND:
            if not self.children_count:
                raise ValueError(f'Compound attributes require a children count > 0')

        if isinstance(self.parent, AttrData):
            self.parent = self.parent.long_name

    @staticmethod
    def enum_str_to_field(enum_names: str) -> TEnumField:
        enum_fields = []
        for n, enum_field in enumerate(enum_names.split(':')):
            if '=' in enum_field:
                split = enum_field.split('=')
                name = split[0]
                value = int(split[1])
            else:
                name = enum_field
                value = n

            enum_fields.append((name, value))

        return enum_fields

class AttrFactory:
    def __new__(cls, data:AttrData) -> om.MFnAttribute:
        """
        Factory class responsible for creating the appropriate function set (MFnAttribute and subclasses) from the data
        that were provided.

        We first find the right function set.
        The next step is to call the create function to actually create the attribute. Different types of attribute will
        have different way to call the create function.
        Finally, we do some post-processing, like adding fields to ENUM attributes, setting the min and max, etc...

        Args:
            data (AttrData): the data to build the MFn from

        Returns:
            MFnAttribute: the new MFnAttribute instance, created and ready to be added to a node
        """

        # CREATE
        # Get the proper function set depending on the AttrType
        mfn = AttrType.to_function_set(data.attr_type)()

        # Call the create appropriate function. Special cases like COLOR and FLOAT3 have a different create function
        if data.attr_type == AttrType.NUMERIC and data.data_type in (DataType.COLOR, DataType.FLOAT3):
            if data.data_type == DataType.COLOR:
                mfn.createColor(*data.create_args)
            elif data.data_type == DataType.FLOAT3:
                mfn.createPoint(*data.create_args)
        else:
            mfn.create(*data.create_args)

        # POST PROCESS
        # For the ENUM type we must add the fields one by one
        # Then we set the default value, which can be an int or a string
        if data.attr_type == AttrType.ENUM:
            for name, value in data.enum_fields:
                mfn.addField(name, value)
            dv = data.default_value
            if isinstance(dv, str):
                mfn.setDefaultByName(dv)
            else:
                # if it's not a string, assume it's an int
                mfn.default = dv

        # For the UNIT and NUMERIC type, set the bounds and soft bounds if any were provided
        if data.attr_type in (AttrType.UNIT, AttrType.NUMERIC):
            if data.min is not None:
                mfn.setMin(data.min)
            if data.max is not None:
                mfn.setMin(data.max)
            if data.soft_min is not None:
                mfn.setMin(data.soft_min)
            if data.soft_max is not None:
                mfn.setMin(data.soft_max)

        # For the STRING type, apply the optional as_filename parameter
        if data.attr_type == AttrType.STRING:
            mfn.usedAsFilename = data.as_filename

        return mfn

class AttributeHandler:
    def __init__(self, node:om.MObject):
        """
        Manages the addition of attributes to a specific node using a DGModifier (or similar). It includes a
        buffer for compound attributes, as they cannot be added to a node if they are empty.

        When a compound attribute is added, it must include a specified children count. Instead of being
        added to the node immediately, the compound attribute is stored in the buffer. As additional attributes
        are added, they can be assigned as children of the pending compound. Once the number of children matches
        the specified count, the compound attribute is added to the node and marked as complete.

        The 'purge' function must be called in conjunction with the 'doIt' function of the modifier. This is done
        automatically if no _modifier is provided in the add_attribute function.

        Args:
            node (MObject): an MObject representing the node to which the attributes will be added
        """
        self.compound_buffer = {}
        self.added_compound = []
        self.node_fn = om.MFnDependencyNode(node)
        self.node_mobj = node

        self._setup_decorator()

    # @add_modifier Dynamically added with _setup_decorator
    def add_attribute(self, fn:om.MFnAttribute, children_count:int=None, parent:str=None, _modifier:DGModifier=None):
        """
        Adds an attribute to a specific node, managing the complexities of compound attributes
        and their children.

        This method handles both regular attributes and compound attributes. Compound attributes are
        buffered until the required number of children is added. Once the children count matches the
        specified value, the compound attribute is added to the node and marked as complete.

        Parameters:
            fn (MFnAttribute): The attribute function set object to be added.
            children_count (int, optional): The number of child attributes required for a compound
                attribute. Defaults to None.
            parent (str, optional): The name of the parent compound attribute, if the attribute being
                added is part of a compound. Defaults to None.
            _modifier (DGModifier, optional): The modifier object used to add the attribute to the node.
                Defaults to None. If the value is None, a default modifier will be used and the doIt function executed.
                Otherwise, executing the doIt function is the user's responsibility, alongside with the purge function

        Notes:
            - This method is dynamically decorated by `add_modifier` in order to provide a default modifier if none was
              given, and execute the doIt function afterward.
            - When compound attributes are added, they are initially stored in a buffer to ensure they
              include the specified number of children.

        Important:
            If a custom modifier is provided by the user, the 'purge' function must be invoked alongside the 'doIt'
            method of the DGModifier to ensure proper finalization of pending operations.
        """
        if parent is None:
            if isinstance(fn, om.MFnCompoundAttribute):
                self._buffer_compound(fn, children_count)
            else:
                self._do_add(fn, _modifier)
        else:
            if self.node_fn.hasAttribute(parent):
                self._do_add(fn, _modifier)
                plug = self.node_fn.findPlug(parent)
                parent_fn = om.MFnCompoundAttribute(plug.attribute())
                parent_fn.addChild(fn.object())
            else:
                parent_fn = self._find_pending_compound(parent)
                parent_fn.addChild(fn)
                self._eval_compound_buffer(parent_fn, _modifier)

    def _find_pending_compound(self, name:str) -> om.MFnCompoundAttribute:
        """
        Searches for a pending compound attribute with the given name in the buffer
        Args:
            name (str): the name of the attribute to look for

        Returns:
            MFnCompoundAttribute: the attribute in the buffer matching the given name

        Raises:
            ValueError : no attribute with the given name was found

        """
        for fn in self.compound_buffer:
            if fn.name == name:
                return fn
        else:
            raise ValueError(f'Could not find an pending compound attribute named {name}')

    def _buffer_compound(self, fn:om.MFnCompoundAttribute, children_count:int):
        """
        Add the given compound attribute to the buffer, along with his expected children count
        Args:
            fn (MFnCompoundAttribute): the attribute to add to the buffer
            children_count (int): the amount of children the attribute should have to be added to the node
        """
        self.compound_buffer[fn] = children_count

    def _is_ready(self, fn:om.MFnCompoundAttribute) -> bool:
        """
        Verifies if the given attribute is ready to be added

        Args:
            fn (MFnCompoundAttribute): the attribute to check

        Returns:
            bool: True if it has enough children, False otherwise

        """
        count = self.compound_buffer[fn][1]
        if fn in self.added_compound:
            return False
        elif fn.numChildren() >= count:
            return True
        else:
            return False

    def _eval_compound_buffer(self, fn:Union[om.MFnCompoundAttribute, None]=None, _modifier:DGModifier=None):
        """
        Adds the pending compound attribute to the node if it is ready. if the attribute is None, check the whole buffer

        Args:
            fn (MFnCompoundAttribute, None): the attribute to check. Checks the whole buffer if the value is None
            _modifier (DGModifier): the modifier used to add the attribute to the node
        """
        if fn is None:
            checklist = self.compound_buffer.keys()
        else:
            checklist = [fn]

        for fn in checklist:
            if self._is_ready(fn):
                self._do_add(fn, _modifier)

    def _do_add(self, fn, _modifier:DGModifier):
        """
        Adds the given attribute to the node

        Args:
            fn (MFnCompoundAttribute): the attribute to add
            _modifier (DGModifier): the modifier used to add the attribute to the node
        """
        _modifier.addAttribute(self.node_mobj, fn.object())
        if fn in self.compound_buffer:
            self.added_compound.append(fn)

    def purge(self):
        """
        Removes the attributes that have been added to the node from the buffer. This function must be called once the
        modifier's doIt function has been called
        """
        # Meant to be called with the doIt function
        for k in self.added_compound:
            self.compound_buffer.pop(k)
        self.added_compound = []

    def _setup_decorator(self):
        """
        Dynamic decoration of add_attribute with the add_modifier decorator in order to call purge alongside with the
        doIt call of the modifier
        """
        self.add_attribute = add_modifier(DGModifier, undo=True, post_call=self.purge)(self.add_attribute)

# ToDo: remove the context ?
class AttrContext:
    def __init__(self, handler:AttributeHandler, modifier:DGModifier, undo:bool=True):
        self.handler = handler
        self.modifier = modifier
        self.undo = undo

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.modifier.doIt()
        if self.undo:
            apiundo.commit(undo=self.modifier.undoIt, redo=self.modifier.doIt)
        self.handler.purge()