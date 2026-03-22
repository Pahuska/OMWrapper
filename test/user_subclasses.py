import sys
from typing import TYPE_CHECKING, Union, List, Tuple

import maya.cmds as cmds
from maya.api import OpenMaya as om
src_root = r'G:\DOCUMENTS\JOB\@PERSO\Tools\OMWrapper'
if src_root not in sys.path:
    sys.path.insert(0, src_root)


from omwrapper.api.utilities import name_to_api
from omwrapper.constants import DataType
from omwrapper.entities.attributes.base import AttrData
from omwrapper.entities.factory import AbstractUserClass, AttrFactory, user_class_manager
from omwrapper.entities.nodes.transform import Transform


class UserTransform(AbstractUserClass, Transform):
    NODE_TYPE = 'UserTransform'
    BASE_CLASS = 'transform'

    @classmethod
    def validator(cls, obj: om.MObject) -> bool:
        fn = om.MFnDependencyNode(obj)
        if fn.hasAttribute('node_type'):
            plug = fn.findPlug('node_type', False)
            if plug.asString() == cls.NODE_TYPE:
                return True
        return False

    @classmethod
    def _pre_create(cls, name) -> Tuple[dict, dict]:
        return {'name':name}, {}

    @classmethod
    def _create(cls, name:str) -> Union[str, om.MObject]:
        node = cmds.createNode(cls.BASE_CLASS, name=name)
        return node

    @classmethod
    def _post_create(cls, node: Union[str, om.MObject], **kwargs):
        mobj = name_to_api(node, True)
        mfn = om.MFnDependencyNode(mobj)
        data = AttrData(long_name='node_type', data_type=DataType.STRING)
        attr = AttrFactory(data)
        mfn.addAttribute(attr.object())
        plug = om.MPlug(mfn.object(), attr.object())
        plug.setString(cls.NODE_TYPE)

class SubUserTransform(UserTransform):
    NODE_TYPE = 'SubUserTransform'

cmds.file(new=True, force=True)

user_class_manager.register(UserTransform, 'validator')
user_class_manager.register(SubUserTransform, 'validator')
node = UserTransform.create('Coucou')
node2 = SubUserTransform.create('Coucou2')