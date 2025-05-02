from typing import TYPE_CHECKING, Union, Tuple, Iterable, List

from maya.api import OpenMaya as om

from omwrapper.api.utilities import name_to_api, TApi
from omwrapper.entities.nodes.dependency import DependNode
from omwrapper.pytools import Iterator

if TYPE_CHECKING:
    from omwrapper.entities.base import MayaObject, recycle_mfn

TSetMemberInput = Union[str, MayaObject, Tuple[om.MDagPath, om.MObject], om.MDagPath, om.MObject, om.MPlug]
TSetMember = Union[om.MObject, Tuple[om.MDagPath, om.MObject], om.MPlug]

class ObjectSet(DependNode):
    _mfn_class = om.MFnSet
    _mfn_constant = om.MFn.kSet

    @recycle_mfn
    def add_member(self, member:TSetMemberInput, mfn:om.MFnSet=None):
        """
        Add a single object to this set

        Args:
            member (TSetMemberInput): The object to add
            mfn (MFnSet, optional): An optional function set representing this node

        Returns:
            None

        """
        member = self._process_member(member)
        mfn.addMember(member)


    @recycle_mfn
    def add_members(self, members:Union[List[TSetMemberInput], om.MSelectionList],
                    mfn:om.MFnSet=None) -> om.MSelectionList:
        """
        Add a list of objects to this set
        Args:
            members (list, MSelectionList): the list of objects to add to the set
            mfn (MFnSet, optional): An optional function set representing this node

        Returns:
            MSelectionList: the list of objects added to this set

        """
        if not isinstance(members, om.MSelectionList):
            members = self._process_members(members=members)
        mfn.addMembers(members)
        return members

    @recycle_mfn
    def get_members(self, flatten:bool=False, as_api:bool=False,  mfn:om.MFnSet=None):
        members = mfn.getMembers(flatten=flatten)
        if as_api:
            return members
        else:
            return self._factory.from_selection_list(members)

    @recycle_mfn
    def remove_member(self, member: TSetMemberInput, mfn: om.MFnSet = None):
        """
        Remove a single object from this set

        Args:
            member (TSetMemberInput): The object to remove
            mfn (MFnSet, optional): An optional function set representing this node

        Returns:
            None

        """
        member = self._process_member(member)
        mfn.removeMember(member)

    @recycle_mfn
    def remove_members(self, members: Union[List[TSetMemberInput], om.MSelectionList],
                    mfn: om.MFnSet = None) -> om.MSelectionList:
        """
        Remove a list of objects from this set
        Args:
            members (list, MSelectionList): the list of objects to remove to the set
            mfn (MFnSet, optional): An optional function set representing this node

        Returns:
            MSelectionList: the list of objects removed to this set

        """
        if not isinstance(members, om.MSelectionList):
            members = self._process_members(members=members)
        mfn.removeMembers(members)
        return members

    @recycle_mfn
    def is_member(self, member:TSetMemberInput, mfn:om.MFnSet=None):
        return mfn.isMember(self._process_member(member))

    @recycle_mfn
    def clear(self, mfn:om.MFnSet=None):
        mfn.clear()

    def _process_member(self, member:TSetMemberInput) -> TSetMember:
        """
        Process an element to make it usable by MFnSet.addMember

        Args:
            member (TSetMemberInput): the input element

        Returns:
            TSetMember: The processed output

        """
        if isinstance(member, str):
            return self._process_member(name_to_api(member))
        elif isinstance(member, MayaObject):
            return member.api_mobject()
        elif isinstance(member, tuple):
            if len(member) != 2:
                raise ValueError('Tuples must have strictly 2 elements')
            if isinstance(member[0], om.MDagPath) and isinstance(member[1], om.MObject):
                return member
            else:
                raise ValueError('Tuples must contain one MDagPath & one MObject')
        elif isinstance(member, om.MDagPath):
            return member.node()
        elif isinstance(member, (om.MObject, om.MPlug)):
            return member
        else:
            raise TypeError(f'Wrong object type : {type(member)}')

    def _process_members(self, members:List[TSetMemberInput]) -> om.MSelectionList:
        """
        Process a list of elements to make it usable by MFnSet.addMembers

        Args:
            members (list): a list of element that will be processed by _process_member

        Returns:
            MSelectionList: a list of all the processed outputs

        """
        it = Iterator(members)
        result = om.MSelectionList()
        while not it.is_done():
            member = self._process_member(it.current_item())
            result.add(member)
            it.next()
        return result
