from omwrapper.constants import ObjectType
from omwrapper.entities.attributes.base import Attribute
from omwrapper.entities.attributes.quantifiable import NumericAttribute, UnitAttribute
from omwrapper.entities.factory import PyObject
from omwrapper.entities.nodes.dag import DagNode
from omwrapper.entities.nodes.dependency import DependNode

pyObject = PyObject()

pyObject.register(ObjectType.DEPEND_NODE, DependNode)
pyObject.register(ObjectType.DAG_NODE, DagNode)

pyObject.register(ObjectType.ATTRIBUTE, Attribute)
pyObject.register(ObjectType.NUMERIC_ATTR, NumericAttribute)
pyObject.register(ObjectType.UNIT_ATTR, UnitAttribute)