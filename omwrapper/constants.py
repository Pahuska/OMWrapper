from enum import Enum
from typing import List, Union, Any, Tuple, Type

from maya.api import OpenMaya as om

class ObjectType(Enum):
    """
    The most basic types of object in Maya
    """
    DEPEND_NODE = 0
    DAG_NODE = 1
    ATTRIBUTE = 2
    COMPONENT = 3

    @classmethod
    def from_mfn(cls, value: int) -> "ObjectType":
        """
        Converts an API MFn constant to an ObjectType
        Args:
            value (MFn constant): the MFn you need to convert

        Returns:
            ObjectType: the converted result

        """
        if value in mfn_to_object_type:
            return mfn_to_object_type[value]
        else:
            raise ValueError(f'No matching ObjectType for MFn constant {value}')

    @classmethod
    def to_mfn(cls, value: "ObjectType") -> int:
        """
        Converts an ObjectType to an API MFn constant
        Args:
            value (ObjectType): the ObjectType you need to convert

        Returns:
            MFn constant: the converted result

        """
        if value in object_type_to_mfn:
            return object_type_to_mfn[value]
        else:
            raise ValueError(f'No matching MFn constant for {value}')

    @classmethod
    def iter_members(cls):
        for member in cls:
            yield member

    @classmethod
    def iter_mfn(cls):
        for member in cls:
            yield cls.to_mfn(member)


object_type_to_mfn = {ObjectType.DEPEND_NODE: om.MFn.kDependencyNode,
                      ObjectType.DAG_NODE: om.MFn.kDagNode,
                      ObjectType.ATTRIBUTE: om.MFn.kAttribute,
                      ObjectType.COMPONENT: om.MFn.kComponent}

mfn_to_object_type = {v: k for k, v in object_type_to_mfn.items()}

class DataType(Enum):
    INVALID = 0
    DISTANCE = 1
    ANGLE = 2
    BOOL = 3
    FLOAT = 4
    INT = 5
    FLOAT2 = 6
    FLOAT3 = 7
    FLOAT4 = 8
    INT2 = 9
    INT3 = 10
    STRING = 11
    MATRIX = 12
    ENUM = 13
    TIME = 14
    MESSAGE = 15
    POINT = 16
    COLOR = 17

    @classmethod
    def from_mobject(cls, MObject: om.MObject) -> "DataType":
        """
        Gets a DataType from the given API MObject.

        Args:
            MObject (MObject): The API object to get the data type for.

        Returns:
            DataType: The data type of the object.
        """
        api_type = MObject.apiType()
        if api_type in [om.MFn.kDoubleLinearAttribute, om.MFn.kFloatLinearAttribute]:
            return cls.DISTANCE
        elif api_type in [om.MFn.kDoubleAngleAttribute, om.MFn.kFloatAngleAttribute]:
            return cls.ANGLE
        elif api_type == om.MFn.kNumericAttribute:
            return cls._from_numeric(om.MFnNumericAttribute(MObject))
        elif api_type in [om.MFn.kAttribute2Double, om.MFn.kAttribute2Float]:
            return cls.FLOAT2
        elif api_type in [om.MFn.kAttribute3Double, om.MFn.kAttribute3Float]:
            mfn = om.MFnAttribute(MObject)
            if mfn.usedAsColor:
                return cls.COLOR
            return cls.FLOAT3
        elif api_type == om.MFn.kAttribute4Double:
            return cls.FLOAT4
        elif api_type in [om.MFn.kAttribute2Int, om.MFn.kAttribute2Short]:
            return cls.INT2
        elif api_type in [om.MFn.kAttribute3Int, om.MFn.kAttribute3Short]:
            return cls.INT3
        elif api_type == om.MFn.kTypedAttribute:
            return cls._from_typed(om.MFnTypedAttribute(MObject))
        elif api_type == om.MFn.kMatrixAttribute:
            return cls.MATRIX
        elif api_type == om.MFn.kEnumAttribute:
            return cls.ENUM
        elif api_type == om.MFn.kTimeAttribute:
            return cls.TIME
        elif api_type == om.MFn.kMessageAttribute:
            return cls.MESSAGE
        else:
            return cls.INVALID

    @classmethod
    def _from_numeric(cls, mfn: om.MFnNumericAttribute) -> "DataType":
        """
        Determines the DataType from a numeric attribute.

        Args:
            mfn (MFnNumericAttribute): The numeric attribute to analyze.

        Returns:
            DataType: The corresponding data type.
        """
        api_type = mfn.numericType()
        if api_type == om.MFnNumericData.kBoolean:
            return cls.BOOL
        elif api_type in [om.MFnNumericData.kShort, om.MFnNumericData.kInt, om.MFnNumericData.kLong, om.MFnNumericData.kByte]:
            return cls.INT
        elif api_type in [om.MFnNumericData.kFloat, om.MFnNumericData.kDouble, om.MFnNumericData.kAddr]:
            return cls.FLOAT
        else:
            raise TypeError(f'Type {mfn.object().apiTypeStr} not supported')

    @classmethod
    def _from_typed(cls, mfn: om.MFnTypedAttribute) -> "DataType":
        """
        Determines the DataType from a typed attribute.

        Args:
            mfn (MFnTypedAttribute): The typed attribute to analyze.

        Returns:
            DataType: The corresponding data type.
        """
        api_type = mfn.attrType()
        if api_type == om.MFnData.kString:
            return cls.STRING
        elif api_type == om.MFnData.kMatrix:
            return cls.MATRIX
        else:
            raise TypeError(f'Type {mfn.object().apiTypeStr} not supported')

    @classmethod
    def to_distance(cls, value: float, unit: int = om.MDistance.uiUnit()) -> om.MDistance:
        """
        Converts a value to a distance.

        Args:
            value (float): The value to convert.
            unit (int, optional): The unit to use. Defaults to MDistance.uiUnit().

        Returns:
            om.MDistance: The converted distance object.
        """
        result = om.MDistance(value, unit)
        return result

    @classmethod
    def to_angle(cls, value: float, unit: int = om.MAngle.uiUnit()) -> om.MAngle:
        """
        Converts a value to an angle.

        Args:
            value (float): The value to convert.
            unit (int, optional): The unit to use. Defaults to MAngle.uiUnit().

        Returns:
            MAngle: The converted angle object.
        """
        result = om.MAngle(value, unit)
        return result

    @classmethod
    def to_euler(cls, value: List[float], order: int = om.MEulerRotation.kXYZ) -> om.MEulerRotation:
        """
        Converts a value to an Euler rotation.

        Args:
            value (list): A sequence of 3 floats representing the rotation.
            order (int, optional): The order of rotation. Defaults to MEulerRotation.kXYZ.

        Returns:
            MEulerRotation: The converted Euler rotation object.
        """
        assert len(value) == 3, 'Value must be a sequence of 3 floats'
        comp = [cls.to_angle(v).asRadians() for v in value]
        comp.append(order)
        return om.MEulerRotation(*comp)

    @classmethod
    def to_time(cls, value: float, unit: int = om.MTime.uiUnit()) -> om.MTime:
        """
        Converts a value to a time object.

        Args:
            value (float): The value to convert.
            unit (int, optional): The unit to use. Defaults to om.MTime.uiUnit().

        Returns:
            MTime: The converted time object.
        """
        result = om.MTime(value, unit)
        return result

    @classmethod
    def to_matrix(cls, value: Union[List[float], List[List[float]]]) -> om.MMatrix:
        """
        Converts a value to a matrix.

        Args:
            value (list): The value to convert. Either a list of 16 floats or a list of 4 lists of 4 floats each

        Returns:
            MMatrix: The converted matrix object.

        Raises:
            ValueError: If the value does not represent a matrix.
        """
        if isinstance(value, (list, tuple)):
            if len(value) == 4 and all(isinstance(x, (list, tuple)) for x in value):
                value = [item for sublist in value for item in sublist]  # Flatten list of lists
                return om.MMatrix(value)
            elif len(value) == 16:
                return om.MMatrix(value)
            else:
                raise ValueError(f'{value} does not represent a matrix')
        else:
            raise ValueError(f'{value} does not represent a matrix')

    @classmethod
    def to_string(cls, value: Any) -> str:
        """
        Converts a value to a string.

        Args:
            value (any): The value to convert.

        Returns:
            str: The converted string.
        """
        result = str(value)
        return result

    @classmethod
    def to_point(cls, value: Union[om.MPoint, List[float]]) -> om.MPoint:
        """
        Converts a value to a point object.

        Args:
            value (MPoint, list): The value to convert.

        Returns:
            MPoint: The converted point object.
        """
        if isinstance(value, om.MPoint):
            return value
        else:
            return om.MPoint(value)

    @classmethod
    def to_vector(cls, value: Union[om.MVector, List[float]]) -> om.MVector:
        """
        Converts a value to a vector object.

        Args:
            value (MVector, list): The value to convert.

        Returns:
            MVector: The converted vector object.
        """
        if isinstance(value, om.MVector):
            return value
        else:
            return om.MVector(value)

    @classmethod
    def numeric(cls) -> Tuple["DataType", ...]:
        """
        List all numeric data types

        Returns:
            list: all numeric data types

        """
        return cls.FLOAT, cls.FLOAT2, cls.FLOAT3, cls.FLOAT4, \
               cls.INT, cls.INT2, cls.INT3, \
               cls.BOOL

    @classmethod
    def unit(cls) -> Tuple["DataType", ...]:
        """
        List all unit data types

        Returns:
            list: all unit data types

        """
        return cls.DISTANCE, cls.ANGLE, cls.TIME

    @classmethod
    def to_api_type(cls, constant:"DataType") -> int:
        """
        Convert a given  unit or numeric DataType into an API constant, such as those found in MFnUnitAttribute and
        MFnNumericAttribute.

        Args:
            constant (DataType): the DataType to convert

        Returns:
            int: the MFnUnitAttribute or MFnNumericAttribute matching the input DataType

        """
        assert constant in cls.numeric() or constant in cls.unit(), f'{constant} is not a Numeric or Unit Type'
        return data_types_to_api[constant]

data_types_to_api = {DataType.DISTANCE: om.MFnUnitAttribute.kDistance,
                     DataType.ANGLE: om.MFnUnitAttribute.kAngle,
                     DataType.TIME: om.MFnUnitAttribute.kTime,
                     DataType.BOOL: om.MFnNumericData.kBoolean,
                     DataType.FLOAT: om.MFnNumericData.kFloat,
                     DataType.FLOAT2: om.MFnNumericData.k2Float,
                     DataType.FLOAT3: om.MFnNumericData.k3Float,
                     DataType.FLOAT4: om.MFnNumericData.k4Double,
                     DataType.INT: om.MFnNumericData.kInt,
                     DataType.INT2: om.MFnNumericData.k2Int,
                     DataType.INT3: om.MFnNumericData.k3Int}

class AttrType(Enum):
    INVALID = 0
    COMPOUND = 1
    ENUM = 2
    GENERIC = 3
    MATRIX = 4
    MESSAGE = 5
    STRING = 6
    NUMERIC = 7
    UNIT = 8

    @classmethod
    def from_data_type(cls, data_type:DataType) -> "AttrType":
        """
        Converts a DataType to the corresponding AttrType.

        Args:
            data_type (DataType): The data type to convert.

        Returns:
            AttrType: The corresponding attribute type. If no match is found, INVALID is returned.
        """

        if data_type in DataType.numeric():
            return cls.NUMERIC
        elif data_type in DataType.unit():
            return cls.UNIT
        elif data_type == DataType.ENUM:
            return cls.ENUM
        elif data_type == DataType.MATRIX:
            return cls.MATRIX
        elif data_type == DataType.MESSAGE:
            return cls.MESSAGE
        elif data_type == DataType.STRING:
            return cls.STRING
        else:
            return cls.INVALID

    @classmethod
    def from_mobject(cls, MObject:om.MObject) -> "AttrType":
        data_type = DataType.from_mobject(MObject)
        if data_type is not DataType.INVALID:
            return cls.from_data_type(data_type)

        api_type = MObject.apiType()
        if api_type == om.MFn.kCompoundAttribute:
            return cls.COMPOUND
        else:
            return cls.INVALID

    @classmethod
    def to_function_set(cls, constant:"AttrType") -> Type[om.MFnAttribute]:
        fn = attr_type_to_function_set.get(constant)
        if fn is None:
            raise TypeError(f'No function set found for AttrType {constant.name}')
        return fn

attr_type_to_function_set = {AttrType.COMPOUND: om.MFnCompoundAttribute,
                             AttrType.ENUM: om.MFnEnumAttribute,
                             AttrType.GENERIC: om.MFnGenericAttribute,
                             AttrType.MATRIX: om.MFnMatrixAttribute,
                             AttrType.MESSAGE: om.MFnMessageAttribute,
                             AttrType.STRING: om.MFnTypedAttribute,
                             AttrType.NUMERIC: om.MFnNumericAttribute,
                             AttrType.UNIT: om.MFnUnitAttribute}