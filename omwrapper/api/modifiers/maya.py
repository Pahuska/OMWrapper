from typing import Any

from maya.api import OpenMaya as om

from omwrapper.api.modifiers.base import AbstractModifier
from omwrapper.constants import DataType


class DGModifier(AbstractModifier, om.MDGModifier):
    # ToDo: implement setPlugValue, connect and disconnect
    def doIt(self) -> None:
        om.MDGModifier.doIt(self)

    def undoIt(self) -> None:
        om.MDGModifier.undoIt(self)

    def create_node(self, node_type:str, name:str=None) -> om.MObject:
        """
        create a node of the given DG type
        Args:
            node_type (str): the type of node (e.g. 'multiplyDivide')
            name (str, optional): the name of the new object

        Returns:
            MObject: the newly create object

        """
        mobj = self.createNode(node_type)
        if name is not None:
            self.renameNode(mobj, name)
        return mobj

    def set_plug_value(self, plug:om.MPlug, value:Any, data_type:DataType=None):
        """
        Sets the value of a specified plug in Maya, handling a variety of data types and plug configurations.

        Args:
            plug (MPlug): The plug whose value is to be set.
            value (Any): The value to assign to the plug. The value's type and format depend on the plug's data type.
            data_type (DataType, optional): The type of the data being set on the plug. If not provided, it is inferred
                                            from the attribute of the plug.

        Raises:
            ValueError: If the plug is a compound attribute and the length of the provided value does not match the number
                        of children plugs.

        Notes:
            - If `value` is an `MObject`, it is assumed to originate from an `MFnData` and directly set using `newPlugValue()`.
            - When `data_type` is not provided, it is determined by examining the plug's attribute.
            - Compound plugs are handled by recursively assigning values to their child plugs.
            - For non-compound plugs, appropriate `newPlugValueXXX` methods are called based on `data_type`.

            Special Handling:
            - `ENUM`: If `value` is a string, it is converted to an integer using `MFnEnumAttribute` before assignment.
            - `MATRIX`: The `value` is converted to an `MFnMatrixData` object before being passed as an `MObject`.
            - Data types such as `ANGLE`, `DISTANCE`, `STRING`, and `TIME` are converted using corresponding `DataType` methods
              if their native types do not match.
        """
        # If the value is an MObject, assume it comes from an MFnData and call it done
        if isinstance(value, om.MObject):
            self.newPlugValue(plug, value)
            return

        # if the data type wasn't provided we need to figure it out
        if data_type is None:
            data_type = DataType.from_mobject(plug.attribute())

        # Handle the compound case
        if plug.isCompound:
            num_children = plug.numChildren()
            if len(value) >= num_children:
                for x in range(num_children):
                    self.set_plug_value(plug.child(x), value[x])
                    return
                else:
                    raise ValueError('Compound Attribute : value length does not match the amount of children')

        # Use the proper newPlugValueXXX method depending on the data type.

        if data_type == DataType.FLOAT:
            self.newPlugValueFloat(plug, value)
        elif data_type == DataType.INT:
            self.newPlugValueInt(plug, value)
        elif data_type == DataType.ENUM:
            if isinstance(value, str):
                mfn = om.MFnEnumAttribute(plug.attribute())
                value = mfn.fieldValue(value)
            self.newPlugValueInt(plug, value)
        elif data_type == DataType.BOOL:
            self.newPlugValueBool(plug, value)
        elif data_type == DataType.ANGLE:
            if not isinstance(value, om.MAngle):
                value = DataType.to_angle(value)
            self.newPlugValueMAngle(plug, value)
        elif data_type == DataType.DISTANCE:
            if not isinstance(value, om.MDistance):
                value = DataType.to_distance(value)
            self.newPlugValueMDistance(plug, value)
        elif data_type == DataType.STRING:
            if not isinstance(value, str):
                value = DataType.to_string(value)
            self.newPlugValueString(plug, value)
        elif data_type == DataType.MATRIX:
            if not isinstance(value, (om.MMatrix, om.MTransformationMatrix)):
                value = DataType.to_matrix(value)
            data = om.MFnMatrixData()
            mobj = data.create(value)
            self.set_plug_value(plug, mobj, DataType.MATRIX)
        elif data_type == DataType.TIME:
            if not isinstance(value, om.MTime):
                value = DataType.to_time(value)
            self.newPlugValueMTime(value)


class DagModifier(DGModifier):
    def create_node(self, node_type:str, name:str=None, parent:om.MObject=om.MObject.kNullObj) -> om.MObject:
        """
        create a node of the given Dag type
        Args:
            node_type (str): the type of node (e.g. 'multiplyDivide')
            name (str, optional): the name of the new object
            parent (MObject, optional): the parent of the object


        Returns:
            MObject: the newly create object

        """
        mobj = self.createNode(node_type, parent=parent)
        if name is not None:
            self.renameNode(mobj, name)
        return mobj