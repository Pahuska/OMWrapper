import sys
from typing import TYPE_CHECKING

import maya.cmds

src_root = r'G:\DOCUMENTS\JOB\@PERSO\Tools\OMWrapper'
if src_root not in sys.path:
    sys.path.insert(0, src_root)

from maya import cmds
from maya.api import OpenMaya as om

from omwrapper.entities.components.mesh import MeshVertex
from omwrapper.entities.nodes.shapes.mesh import Mesh
from omwrapper.entities.nodes.dag import DagNode
from omwrapper.general import pyobject, select
if TYPE_CHECKING:
    from omwrapper.entities.nodes.transform import Transform
    from omwrapper.entities.nodes.dependency import DependNode

cmds.file(new=True, force=True)

sphere = pyobject(f'{cmds.polySphere()[0]}') # type: Transform
curve = pyobject(f'{cmds.circle()[0]}') # type: Transform
plane = pyobject(f'{cmds.nurbsPlane()[0]}') # type: Transform

select(sphere)
sphere.scale.set([5,5,5])

lattice = pyobject(f'{cmds.lattice()[1]}') # type: Transform
ffd = pyobject('ffd1') # type: DependNode


sphere.vtx[2].set_position([10,10,10], 0)
curve.cv[2].set_position([10,10,10], 0)
plane.cv[0][2].set_position([10,10,10], 0)
lattice.pt[0][1][1].set_position([10, 10, 10], 0)
ffd.outsideLattice.set(1)