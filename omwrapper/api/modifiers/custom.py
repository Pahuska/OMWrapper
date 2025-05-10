from typing import Union, Callable, List

from omwrapper.api.modifiers.base import AbstractModifier, TModifier
from omwrapper.pytools import Iterator


class CompoundModifier(AbstractModifier):
    def __init__(self, *args: TModifier):
        """
        Not an actual modifier but a compound of modifiers. The doIt and undoIt methods will iterate through all the
        modifiers in the compound and execute the corresponding methods

        Args:
            *args (MDGModifier, MDagModifier, AbstractModifier): basically any modifier-like object that has the two
            required methods doIt and undoIt
        """
        self.modifiers = list(args)

    def append(self, modifier: TModifier):
        """
        Adds a new modifier to the compound
        Args:
            modifier(MDGModifier, MDagModifier, AbstractModifier): basically any modifier-like object that has the two
            required methods doIt and undoIt

        Returns:
            None

        """
        self.modifiers.append(modifier)

    def extend(self, iterable:List[TModifier]):
        """
        Adds a new list of modifiers to the compound
        Args:
            iterable (List): a list of any modifier-like object that has the two
            required methods doIt and undoIt

        Returns:
            None

        """
        self.modifiers.extend(iterable)

    def get_iterator(self) -> Iterator:
        """
        Get an Iterator object with the list of modifiers in this compound

        Returns:
            Iterator

        """
        return Iterator(self.modifiers)

    def doIt(self):
        """
        Iterate through all the modifiers and execute the doIt function

        Returns:
            None
        """
        it = self.get_iterator()
        while not it.is_done():
            it.current_item().doIt()
            it.next()

    def undoIt(self):
        """
        Iterate through all the modifiers and execute the undoIt function

        Returns:
            None
        """
        # ToDo: should we reverse the list of modifiers for this ?
        it = self.get_iterator()
        while not it.is_done():
            it.current_item().undoIt()
            it.next()


class ProxyModifier(AbstractModifier):
    def __init__(self, do_func:Callable, do_args:Union[list, tuple]=None, do_kwargs:dict=None,
                 undo_func:Callable=None, undo_args:Union[list, tuple]=None, undo_kwargs:dict=None):
        """
        A Proxy of a modifier to allow user to pass their own undo and redo functions
        Args:
            do_func (Callable): the function executed in doIt
            do_args (List, Tuple, optional): the args for the doIt function
            do_kwargs (Dict, optional): the keyword args for the doIt function
            undo_func (Callable, optional): the function executed in undoIt. Same as do_func if none is provided
            undo_args (List, Tuple, optional): the args for the undoIt function
            undo_kwargs (Dict, optional): the keyword args for the undoIt function
        """
        self._do_it = do_func
        if undo_func is None:
            self._undo_it = self._do_it
        else:
            self._undo_it = undo_func

        if do_args is None:
            self._do_args = ()
        else:
            self._do_args = do_args

        if undo_args is None:
            self._undo_args = ()
        else:
            self._undo_args = undo_args

        if do_kwargs is None:
            self._do_kwargs = {}
        else:
            self._do_kwargs = do_kwargs

        if undo_kwargs is None:
            self._undo_kwargs = {}
        else:
            self._undo_kwargs = undo_kwargs

    def doIt(self):
        return self._do_it(*self._do_args, **self._do_kwargs)

    def undoIt(self):
        return self._undo_it(*self._undo_args, **self._undo_kwargs)