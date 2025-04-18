from typing import Dict

from maya.api import OpenMaya as om

from omwrapper.api.modifiers.base import TModifier, add_modifier
from omwrapper.api.modifiers.custom import ProxyModifier
from omwrapper.api.modifiers.maya import DGModifier
from omwrapper.api.utilities import name_to_api
from omwrapper.entities.attributes.base import AttributeHandler, AttrData, AttrFactory
from omwrapper.entities.base import MayaObject, TMayaObjectApi, recycle_mfn
from omwrapper.api import apiundo


class DependNode(MayaObject):
    _mfn_class = om.MFnDependencyNode
    _mfn_constant = om.MFn.kDependencyNode

    def __init__(self, **kwargs: TMayaObjectApi):
        super().__init__(**kwargs)
        self._attribute_handler = AttributeHandler(self.api_mobject())

    def __getattr__(self, item):
        print(f'getting attribute {item}')
        attr = self.attr(item)
        setattr(self, item, attr)

    def api_mfn(self) -> om.MFnDependencyNode:
        return self._mfn_class(self.api_mobject())

    def name(self, full_dag_path:bool=False) -> str:
        mfn = om.MFnDependencyNode(self.api_mobject())
        return mfn.name()

    @classmethod
    def get_build_data_from_name(cls, name:str) -> Dict[str, TMayaObjectApi]:
        mobj = name_to_api(name)
        if not isinstance(mobj, om.MObject):
            raise TypeError(f'{name} is not a Dependency Node')

        return {'MObjectHandle': om.MObjectHandle(mobj)}

    @recycle_mfn
    def rename_(self, name:str, mfn:om.MFnDependencyNode) -> str:
        """
        Rename the node - NOT UNDOABLE -

        Args:
            name (str): the new name of the node
            mfn (MFnDependencyNode, optional): an optional compatible MFn.

        Returns:
            str: the new name of the node

        """
        name = mfn.setName(name)
        return name

    @add_modifier(DGModifier, undo=True)
    def rename(self, name:str, _modifier:TModifier) -> str:
        """
        Rename the node

        Args:
            name (str): the new name of the node
            _modifier (AbstractModifier, MDGModifier, MDagModifier, optional): an optional modifier object. if one is
                provided, it will be up to the user to execute the doIt function and handle the undo behavior

        Returns:
            str: the new name of the node

        """
        _modifier.renameNode(self.api_mobject(), name)
        return self.name()

    def has_attr(self, name:str) -> bool:
        """
        Verify whether an attribute with the given name exists on this node

        Args:
            name (str): the name of the attribute

        Returns:
            bool: True if it exists, False otherwise

        """
        mfn = om.MFnDependencyNode(self.api_mobject())
        return mfn.hasAttribute(name)

    def add_attr(self, data:AttrData, _modifier:DGModifier=None):
        """
        Adds a new attribute to this node, based on the provided AttrData. Search AttrData's doc for more information.
        An optional _modifier can be passed. In that case it is up to the user to trigger the doIt function, and then
        purge this node's AttributeHandler buffer. This can also be done with an AttrContext. Check examples below

        Args:
            data (AttrData): the data needed to create the attribute
            _modifier: an optional DGModifier or similar

        Returns:
            None

        Examples:
            # Create the AttrData objects
            ikfk = AttrData('ikfk', data_type=DataType.BOOL, default_value=True, keyable=True)
            compound = AttrData('attr_group', attr_type=AttrType.COMPOUND, children_count=3)
            float_a = AttrData('float_a', data_type=DataType.FLOAT, min=-10, max=10, default_value=1.0, parent=compound,
                               keyable=True)
            enum_b = AttrData('enum_b', attr_type=AttrType.ENUM, enum_names='yellow=0:red=10:blue=100', parent='attr_group',
                              keyable=True)
            string_c = AttrData('string_c', attr_type=AttrType.STRING, default_value='coucou', parent=compound, keyable=True)

            py_node = pyObject(cmds.polySphere()[0]) # type: DependNode
            attributes = [ikfk, compound, float_a, enum_b,string_c]

            # Create the attributes using the simple method
            for at in attributes:
                py_node.add_attr(at)

            # Create the attributes with an AttrContext
            py_node = pyObject(cmds.polySphere()[0]) # type: DependNode
            mod = DGModifier()
            with AttrContext(py_node.attr_handler(), mod, undo=True):
                for at in attributes:
                    py_node.add_attr(at, _modifier=mod)

            # Create the attribute and purging manually
            py_node = pyObject(cmds.polySphere()[0]) # type: DependNode
            mod = DGModifier()
            for at in attributes:
                py_node.add_attr(at, _modifier=mod)
            mod.doIt()  # Executing the modifier
            node.attribute_handler().purge()    # Purging the buffer of the attribute_handler
            apiundo.commit(undo=mod.undoIt, redo=mod.doIt)  # Adding this operation to the undo queue (optional)
        """
        fn = AttrFactory(data)

        # Make sure the name of the attribute is not already in use on this node
        names = (data.long_name, data.short_name)
        for n in names:
            if self.has_attr(n):
                raise NameError(f'there is already an attribute named {n}')

        self._attribute_handler.add_attribute(fn=fn, children_count=data.children_count,
                                              parent=data.parent, _modifier=_modifier)

    def attr_handler(self) -> AttributeHandler:
        """
        Get the AttributeHandler that manages the addition of attributes for this node
        Returns:
            AttributeHandler: the AttributeHandler of this node

        """
        return self._attribute_handler

    def attr(self, name):
        if self.has_attr(name):
            mfn = om.MFnDependencyNode(self.api_mobject())
            plug = mfn.findPlug(name, False)
            attr = self._factory(MPlug=plug, MObjectHandle=om.MObjectHandle(plug.attribute()), node=self)
            return attr
        else:
            raise AttributeError(f'{self.name()} has no attribute named {name}')

    @recycle_mfn
    def is_locked(self, mfn:om.MFnDependencyNode) -> bool:
        """
        Whether this node is locked or not

        Returns:
            bool: True if the node is locked, False otherwise
            mfn (MFnDependencyNode, optional): an optional compatible MFn.

        """
        locked = mfn.isLocked
        return locked

    @recycle_mfn
    def set_locked_(self, value:bool, mfn:om.MFnDependencyNode):
        mfn.isLocked = value

    @recycle_mfn
    def set_locked(self, value:bool, mfn:om.MFnDependencyNode):
        old_value = mfn.isLocked
        modifier = ProxyModifier(do_func=self.set_locked_, do_kwargs={'value':value, 'mfn':mfn},
                                 undo_kwargs={'value':old_value, 'mfn':mfn})
        modifier.doIt()

        apiundo.commit(undo=modifier.undoIt, redo=modifier.doIt)

        return modifier