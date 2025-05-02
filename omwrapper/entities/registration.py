from omwrapper.constants import ObjectType, AttributeType, DagNodeType, DependNodeType
from omwrapper.entities.attributes.base import Attribute
from omwrapper.entities.attributes.compound import CompoundAttribute
from omwrapper.entities.attributes.quantifiable import NumericAttribute, UnitAttribute
from omwrapper.entities.factory import PyObject
from omwrapper.entities.nodes.dag import DagNode
from omwrapper.entities.nodes.dependency import DependNode
from omwrapper.entities.nodes.joint import Joint
from omwrapper.entities.nodes.objectset import ObjectSet
from omwrapper.entities.nodes.shapes.lattice import LatticeShape
from omwrapper.entities.nodes.shapes.mesh import Mesh
from omwrapper.entities.nodes.shapes.nurbs import NurbsCurve, NurbsSurface
from omwrapper.entities.nodes.transform import Transform

pyObject = PyObject()

pyObject.register(ObjectType.DEPEND_NODE, DependNode)
pyObject.register(DependNodeType.OBJECT_SET, ObjectSet)

pyObject.register(ObjectType.DAG_NODE, DagNode)
pyObject.register(DagNodeType.TRANSFORM, Transform)
pyObject.register(DagNodeType.JOINT, Joint)
pyObject.register(DagNodeType.MESH, Mesh)
pyObject.register(DagNodeType.NURBS_CURVE, NurbsCurve)
pyObject.register(DagNodeType.NURBS_SURFACE, NurbsSurface)
pyObject.register(DagNodeType.LATTICE_SHAPE, LatticeShape)

pyObject.register(ObjectType.ATTRIBUTE, Attribute)
pyObject.register(AttributeType.NUMERIC, NumericAttribute)
pyObject.register(AttributeType.UNIT, UnitAttribute)
pyObject.register(AttributeType.COMPOUND, CompoundAttribute)