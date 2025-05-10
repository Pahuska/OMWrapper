import sys
from typing import TYPE_CHECKING

src_root = r'G:\DOCUMENTS\JOB\@PERSO\Tools\OMWrapper'
if src_root not in sys.path:
    sys.path.insert(0, src_root)

from maya import cmds
from maya.api import OpenMaya as om

from omwrapper.reload import reload_modules
reload_modules()

from omwrapper.api.modifiers.maya import DGModifier
from omwrapper.constants import AttrType, DataType
from omwrapper.entities.attributes.base import AttrData, AttrContext
from omwrapper.entities.nodes.dependency import DependNode
from omwrapper.general import pyobject, create_node

cmds.file(new=True, force=True)

if TYPE_CHECKING:
    from omwrapper.entities.nodes.objectset import ObjectSet
    from omwrapper.entities.nodes.transform import Transform

#NODE MANIPULATION

node = create_node('transform', name='node_a') #type: Transform
child = create_node('transform', name='child_a', parent=node)
node.rename('NodeA')

# ATTRIBUTE CREATION

# Creating the AttrData objects
ikfk = AttrData('ikfk', data_type=DataType.BOOL, default_value=True, keyable=True)
compound = AttrData('attr_group', attr_type=AttrType.COMPOUND, children_count=3)
float_a = AttrData('float_a', data_type=DataType.FLOAT, min=-10, max=10, default_value=1.0, parent=compound,
                   keyable=True, multi=True)
enum_b = AttrData('enum_b', attr_type=AttrType.ENUM, enum_names='yellow=0:red=10:blue=100', parent='attr_group',
                  keyable=True)
string_c = AttrData('string_c', attr_type=AttrType.STRING, default_value='coucou', parent=compound, keyable=True)

vector_d = AttrData('vector_d', data_type=DataType.FLOAT3, default_value=om.MVector.kXaxisVector, keyable=True)

print(node.has_attr('translateW'))

attributes = [ikfk, compound, float_a, enum_b,string_c, vector_d]

for at in attributes:
    node.add_attr(at)

py_node = pyobject(cmds.polySphere()[0]) # type: DependNode
mod = DGModifier()
with AttrContext(py_node.attr_handler(), mod, undo=True):
    for at in attributes:
        py_node.add_attr(at, _modifier=mod)

attribute = pyobject('persp.translateX')

new_set = cmds.sets(node, child, node.float_a[0])
object_set = pyobject(new_set) #type: ObjectSet
object_set.add_member(py_node)
object_set.add_member(node.ikfk)

cmds.select(node, child)

n = node.float_a.name()
print(n)