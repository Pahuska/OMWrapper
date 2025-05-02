import sys

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
from omwrapper.pytools import Timer

from omwrapper.general import pyObject

cmds.file(new=True, force=True)

# Creating the AttrData objects
ikfk = AttrData('ikfk', data_type=DataType.BOOL, default_value=True, keyable=True)
compound = AttrData('attr_group', attr_type=AttrType.COMPOUND, children_count=3)
float_a = AttrData('float_a', data_type=DataType.FLOAT, min=-10, max=10, default_value=1.0, parent=compound,
                   keyable=True)
enum_b = AttrData('enum_b', attr_type=AttrType.ENUM, enum_names='yellow=0:red=10:blue=100', parent='attr_group',
                  keyable=True)
string_c = AttrData('string_c', attr_type=AttrType.STRING, default_value='coucou', parent=compound, keyable=True)

vector_d = AttrData('vector_d', data_type=DataType.FLOAT3, default_value=om.MVector.kXaxisVector, keyable=True)

node = cmds.polySphere()[0]
py_node = pyObject(node)
py_node.rename('pCube3')
print(py_node.has_attr('translateW'))

attributes = [ikfk, compound, float_a, enum_b,string_c, vector_d]

for at in attributes:
    py_node.add_attr(at)

py_node = pyObject(cmds.polySphere()[0]) # type: DependNode
mod = DGModifier()
with AttrContext(py_node.attr_handler(), mod, undo=True):
    for at in attributes:
        py_node.add_attr(at, _modifier=mod)

attribute = pyObject('persp.translateX')
at = py_node.vector_d