from omwrapper.constants import ObjectType, AttributeType, DagNodeType, DependNodeType
from omwrapper.entities.attributes.base import Attribute, MultiAttribute
from omwrapper.entities.attributes.compound import CompoundAttribute
from omwrapper.entities.attributes.quantifiable import NumericAttribute, UnitAttribute
from omwrapper.entities.factory import PyObject, BaseSelector, AttributeSelector
from omwrapper.entities.nodes.dag import DagNode
from omwrapper.entities.nodes.dependency import DependNode
from omwrapper.entities.nodes.joint import Joint
from omwrapper.entities.nodes.objectset import ObjectSet
from omwrapper.entities.nodes.shapes.lattice import LatticeShape
from omwrapper.entities.nodes.shapes.mesh import Mesh
from omwrapper.entities.nodes.shapes.nurbs import NurbsCurve, NurbsSurface
from omwrapper.entities.nodes.transform import Transform

pyobject = PyObject()

depend_node_selector = BaseSelector(ObjectType.DEPEND_NODE)
depend_node_selector.register(ObjectType.DEPEND_NODE, DependNode)
depend_node_selector.register(DependNodeType.OBJECT_SET, ObjectSet)

dag_node_selector = BaseSelector(ObjectType.DAG_NODE)
dag_node_selector.register(ObjectType.DAG_NODE, DagNode)
dag_node_selector.register(DagNodeType.TRANSFORM, Transform)
dag_node_selector.register(DagNodeType.JOINT, Joint)
dag_node_selector.register(DagNodeType.MESH, Mesh)
dag_node_selector.register(DagNodeType.NURBS_CURVE, NurbsCurve)
dag_node_selector.register(DagNodeType.NURBS_SURFACE, NurbsSurface)
dag_node_selector.register(DagNodeType.LATTICE_SHAPE, LatticeShape)

attribute_selector = AttributeSelector(ObjectType.ATTRIBUTE)
attribute_selector.register(ObjectType.ATTRIBUTE, Attribute)
attribute_selector.register(attribute_selector.MULTI, MultiAttribute)
attribute_selector.register(AttributeType.NUMERIC, NumericAttribute)
attribute_selector.register(AttributeType.UNIT, UnitAttribute)
attribute_selector.register(AttributeType.COMPOUND, CompoundAttribute)

pyobject.register(ObjectType.DEPEND_NODE, depend_node_selector)
pyobject.register(ObjectType.DAG_NODE, dag_node_selector)
pyobject.register(ObjectType.ATTRIBUTE, attribute_selector)