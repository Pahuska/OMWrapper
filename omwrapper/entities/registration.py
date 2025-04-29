from omwrapper.constants import ObjectType, AttributeType, DagNodeType
from omwrapper.entities.attributes.base import Attribute
from omwrapper.entities.attributes.quantifiable import NumericAttribute, UnitAttribute
from omwrapper.entities.factory import PyObject
from omwrapper.entities.nodes.dag import DagNode
from omwrapper.entities.nodes.dependency import DependNode
from omwrapper.entities.nodes.transform import Transform

pyObject = PyObject()

pyObject.register(ObjectType.DEPEND_NODE, DependNode)
pyObject.register(ObjectType.DAG_NODE, DagNode)
pyObject.register(DagNodeType.TRANSFORM, Transform)

pyObject.register(ObjectType.ATTRIBUTE, Attribute)
pyObject.register(AttributeType.NUMERIC, NumericAttribute)
pyObject.register(AttributeType.UNIT, UnitAttribute)