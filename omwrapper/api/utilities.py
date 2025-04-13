from functools import wraps
from typing import Union, Tuple, Any

from maya.api import OpenMaya as om

from omwrapper.api import apiundo
from omwrapper.constants import DataType

def unique_object_exists(name:str) -> bool:
    """
    Checks if a unique object with the given name exists in the current scene.
    To do so we pass the object through an MSelectionList and if catch any error returned.
    Args:
        name (str): the name of any maya object

    Returns:
        bool: True if the unique object exists, False otherwise

    """
    try:
        sel = om.MSelectionList()
        sel.add(name)
        return True
    except:
        return False

TApi = Union[om.MObject, om.MDagPath, om.MPlug, Tuple[om.MDagPath, om.MObject]]
def name_to_api(name:str, as_mobject:bool = False) -> TApi:
    """
    Finds the API object that corresponds to the given name
    Args:
        name (str): the name of any maya object
        as_mobject (bool): if True, the returned object will be an MObject.

    Returns:
        MObject: if the given object is a DependNode or if as_mobject was set to true
        MPlug: if the given object is an attribute
        tuple: if the given object is a component, a tuple containing an MDagPath and an MObject
        MDagPath: if the given object is a DagNode

    """
    if not unique_object_exists(name):
        raise NameError('{} does not exist or is not unique'.format(name))

    sel = om.MSelectionList()
    sel.add(name)

    if '.' in name:     # In that case we either have a Plug or a Component
        try:
            plug = sel.getPlug(0)
            if as_mobject:
                return plug.attribute()
            else:
                return plug
        except TypeError:
            try:
                comp = sel.getComponent(0)
                if as_mobject:
                    return comp[1]
                else:
                    return comp
            except RuntimeError:
                raise TypeError(f'cannot find an attribute or a component named {name}')
    else:       # Figure out if it's a DAG or DG
        try:
            dag = sel.getDagPath(0)
            if as_mobject:
                return dag.node()
            else:
                return dag
        except TypeError:
            obj = sel.getDependNode(0)
            return obj

def api_undo(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        result = func(*args, **kwargs)
        if result is not None:
            apiundo.commit(undo=result.undoIt, redo=result.doIt)
        return result
    return wrapped

def get_plug_value(plug:om.MPlug, data_type:DataType=None, as_string:bool=False,
                   context:om.MDGContext=om.MDGContext.kNormal) -> Any:
    """
    Retrieves the value of a specified plug in Maya, handling various data types and plug configurations.

    Args:
        plug (MPlug): The plug whose value is to be retrieved.
        data_type (DataType, optional): The expected type of the plug's value. If not provided, the type is inferred
                                        from the plug's attribute.
        as_string (bool, optional): If True, for enum plugs, the value is returned as a string corresponding to the
                                    field name. Defaults to False.
        context (MDGContext, optional): The evaluation context (aka time) to use when fetching the plug value. Defaults
                                       to `MDGContext.kNormal`.

    Returns:
        Any: The value of the plug, in the format corresponding to its data type.
             - For compound plugs, a list of values is returned, one for each child plug.
             - For vector plugs (e.g., FLOAT3, INT3), an `MVector` may be returned.
             - For matrix plugs, an `MMatrix` is returned.
             - For message plugs, the connected source node is returned if applicable, or `None` otherwise.

    Raises:
        TypeError: If the plug's data type is unsupported.

    Notes:
        - Compound plugs are handled by recursively retrieving values for their child plugs.
        - For data types like DISTANCE, ANGLE, and TIME, unit conversions are performed based on the UI unit of the plug.
        - Enum plugs can optionally return their value as a string using the `as_string` flag.
        - Unsupported data types will result in a `TypeError`.

        Special Handling:
        - FLOAT2, FLOAT3, FLOAT4, INT2, INT3: Values are retrieved for each child plug and combined into a list or vector.
        - MATRIX: Values are extracted using `MFnMatrixData` and returned as an `MMatrix`.
        - MESSAGE: Returns the connected source node for destination plugs, or `None` if no connection exists.
    """
    # In case of a compound, loop through all the children and return a list of all the values
    if plug.isCompound:
        num_children = plug.numChildren()
        value = []
        for x in range(num_children):
            value.append(get_plug_value(plug, data_type=None, as_string=as_string, context=context))
        return value

    # if the data type wasn't provided we need to figure it out
    if data_type is None:
        data_type = DataType.from_mobject(plug.attribute())

    if data_type == DataType.DISTANCE:
        d = plug.asMDistance(context)
        return d.asUnits(d.uiUnit())

    elif data_type == DataType.ANGLE:
        a = plug.asMAngle(context)
        return a.asUnits(a.uiUnit())

    elif data_type == DataType.FLOAT:
        return plug.asFloat(context)

    elif data_type == DataType.BOOL:
        return plug.asBool(context)

    elif data_type == DataType.INT:
        return plug.asInt(context)

    elif data_type == DataType.ENUM:
        if as_string:
            e = om.MFnEnumAttribute(plug.attribute())
            return e.fieldName(plug.asInt(context))
        else:
            return plug.asInt(context)

    elif data_type == DataType.STRING:
        return plug.asString(context)

    elif data_type == DataType.TIME:
        t = plug.asMTime(context)
        return t.asUnits(t.uiUnit())

    elif data_type in (DataType.FLOAT2, DataType.FLOAT3, DataType.FLOAT4, DataType.INT2, DataType.INT3):
        value = [get_plug_value(plug.child(x), context=context) for x in range(plug.numChildren())]
        if data_type in (DataType.FLOAT3, DataType.INT3):
            return om.MVector(value)
        return value

    elif data_type == DataType.MATRIX:
        mobj = plug.asMObject(context)
        matrix = om.MFnMatrixData(mobj).matrix()
        return om.MMatrix(matrix)

    elif data_type == DataType.MESSAGE:
        if plug.isDestination:
            return plug.source().node()
        else:
            return None
    else:
        raise TypeError('Unsupported plug type')