import sys
src_root = r'G:\DOCUMENTS\JOB\@PERSO\Tools\OMWrapper'
if src_root not in sys.path:
    sys.path.insert(0, src_root)

from maya import cmds

from omwrapper.reload import reload_modules

reload_modules()

from omwrapper.general import pyObject

cmds.file(new=True, force=True)
node = cmds.polySphere()[0]

py_node = pyObject(node)
py_node.rename('pCube3')
print(py_node.has_attr('translateW'))