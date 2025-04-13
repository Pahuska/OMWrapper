from omwrapper.constants import ObjectType
from omwrapper.entities.factory import PyObject
from omwrapper.entities.nodes.dependency import DependNode

pyObject = PyObject()

pyObject.register(ObjectType.DEPEND_NODE, DependNode)