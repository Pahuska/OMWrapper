from typing import List, Union

from maya.api import OpenMaya as om

from omwrapper.api import apiundo
from omwrapper.api.modifiers.base import add_modifier
from omwrapper.api.modifiers.custom import ProxyModifier
from omwrapper.api.modifiers.maya import DagModifier
from omwrapper.entities.base import recycle_mfn
from omwrapper.entities.nodes.dag import DagNode


class Transform(DagNode):
    _mfn_class = om.MFnTransform
    _mfn_constant = om.MFn.kTransform

    def api_mfn(self) -> om.MFnTransform:
        return super().api_mfn()

    def shape_count(self):
        dag = self.api_dagpath()
        return dag.numberOfShapesDirectlyBelow()

    def get_shape(self, n:int=0) -> DagNode:
        dag = self.api_dagpath()
        if n >= dag.numberOfShapesDirectlyBelow():
            raise ValueError(f'{self.name()} : shape index {n} out of range')

        dag = om.MDagPath(dag)
        dag.extendToShape(n)

        sel = om.MSelectionList()
        sel.add(dag)
        return self._factory(MObjectHandle=om.MObjectHandle(sel.getDependNode(0)), MDagPath=dag)

    def get_shapes(self) -> List[DagNode]:
        for x in range(self.shape_count()):
            yield self.get_shape(x)

    def has_attr(self, name:str, check_shape:bool=True) -> bool:
        result = super().has_attr(name=name)
        if result:
            return result
        elif check_shape:
            for shape in self.get_shapes():
                if shape.has_attr(name):
                    return True

    def attr(self, name:str, check_shape:bool=True):
        if self.has_attr(name, False):
            return super().attr(name=name)
        elif check_shape:
            for shape in self.get_shapes():
                if shape.has_attr(name):
                    return shape.attr(name)
        else:
            raise ValueError(f'No attribute named {name}')

    @recycle_mfn
    def set_matrix_(self, matrix:Union[om.MMatrix, om.MTransformationMatrix], space:int=om.MSpace.kObject,
                    mfn:om.MFnTransform=None):
        if not isinstance(matrix, om.MTransformationMatrix):
            matrix = om.MTransformationMatrix(matrix)

        if space == om.MSpace.kWorld:
            pim = self.parentInverseMatrix.get()
            m = matrix.asMatrix()
            matrix = om.MTransformationMatrix(m*pim)

        mfn.setTransformation(matrix)

    def get_matrix(self, space:int=om.MSpace.kObject):
        if space == om.MSpace.kObject:
            return self.matrix.get()
        elif space == om.MSpace.kWorld:
            return self.worldMatrix.get()
        else:
            raise ValueError('get_matrix : Invalid MSpace constant. Accepted spaces are kObject or kWorld')

    def set_matrix(self, matrix:Union[om.MMatrix, om.MTransformationMatrix], space:int=om.MSpace.kObject):
        do_kwargs = {'matrix':matrix, 'space':space}
        undo_kwargs = {'matrix':self.get_matrix(space=space), 'space':space}
        mod = ProxyModifier(do_func=self.set_matrix_, do_kwargs=do_kwargs, undo_kwargs=undo_kwargs)
        mod.doIt()
        apiundo.commit(undo=mod.undoIt, redo=mod.doIt)

    @recycle_mfn
    def get_rotation(self, space:int=om.MSpace.kTransform, as_quaternion:bool=False, mfn:om.MFnTransform=None):
        return mfn.rotation(space, asQuaternion=as_quaternion)