from omwrapper.constants import ObjectType
from omwrapper.entities.attributes.base import Attribute
from omwrapper.entities.factory import PyObject
from omwrapper.entities.nodes.dag import DagNode
from omwrapper.entities.nodes.dependency import DependNode

pyObject = PyObject()

pyObject.register(ObjectType.DEPEND_NODE, DependNode)
pyObject.register(ObjectType.ATTRIBUTE, Attribute)
pyObject.register(ObjectType.DAG_NODE, DagNode)