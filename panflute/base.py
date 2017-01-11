"""
Base classes and methods of all Pandoc elements
"""

# ---------------------------
# Imports
# ---------------------------

# from operator import attrgetter
from collections import OrderedDict
from itertools import chain

from .containers import ListContainer, DictContainer
from .utils import check_type, encode_dict, check_group
from .constants import *

# import sys
from typing import List, AnyStr, Dict


# ---------------------------
# Meta Classes
# ---------------------------


class Element(object):
    """
    Base class of all Pandoc elements
    """
    __slots__ = ['parent', 'location', 'identifier', 'classes', 'attributes', '_content']
    _children = []
    child_type = None

    def __init__(self, identifier: str=None, parent: 'Element'=None, location=None):
        self.identifier = identifier
        self.parent = parent
        self.location = location
        self._content = None

    @property
    def tag(self):
        tag = type(self).__name__
        return tag

    # ---------------------------
    # Base methods
    # ---------------------------
    # Should be overridden except for trivial elements (Space, Null, etc.)

    def __repr__(self):
        # This is just a convenience method
        # Override it for more complex elements

        extra = []
        for key in self.__slots__:
            if not key.startswith('_') and key != 'text':
                val = getattr(self, key)
                if val not in ([], OrderedDict(), ''):
                    extra.append([key, val])

        if extra:
            extra = ('{}={}'.format(k, repr(v)) for k, v in extra)
            extra = '; ' + ', '.join(x for x in extra)
        else:
            extra = ''

        if '_content' in self.__slots__:
            content = ' '.join(repr(x) for x in self.content)
            return '{}({}{})'.format(self.tag, content, extra)
        elif 'text' in self.__slots__:
            return '{}({}{})'.format(self.tag, self.text, extra)
        else:
            return self.tag

    def to_json(self):
        return encode_dict(self.tag, self._slots_to_json())

    def _slots_to_json(self):
        # Default when the element contains nothing
        return []

    # ---------------------------
    # .identifier .classes .attributes
    # ---------------------------

    def _set_ica(self, identifier, classes, attributes):
        self.identifier = check_type(identifier, str)
        self.classes = [check_type(cl, str) for cl in classes]
        self.attributes = OrderedDict(attributes)

    def _ica_to_json(self):
        return [self.identifier, self.classes, list(self.attributes.items())]

    # ---------------------------
    # .content (setter and getter)
    # ---------------------------

    @property
    def content(self) -> ListContainer:
        """
        Sequence of :class:`Element` objects (usually either :class:`Block`
        or :class:`Inline`) that are "children" of the current element.

        Only available for elements that accept ``*args``.

        Note: some elements have children in attributes other than ``content``
        (such as :class:`.Table` that has children in the header and
        caption attributes).
        """
        return self._content

    @content.setter
    def content(self, value):
        oktypes = self._content.oktypes
        self._content = ListContainer(value, oktypes=oktypes, parent=self)

    def _set_content(self, value, oktypes):
        """
        Similar to content.setter but when there are no existing oktypes
        """
        if value is None:
            value = []
        self._content = ListContainer(value, oktypes=oktypes, parent=self)

    # ---------------------------
    # Navigation
    # ---------------------------

    @property
    def index(self):
        """
        Return position of element inside the parent.

        :rtype: ``int`` | ``None``
        """
        container = self.container
        if container is not None:
            return container.index(self)

    @property
    def container(self):
        """
        Rarely used attribute that returns the ``ListContainer`` or
        ``DictContainer`` that contains the element
        (or returns None if no such container exist)

        :rtype: ``ListContainer`` | ``DictContainer`` | ``None``
        """
        if self.parent is None:
            return None
        elif self.location is None:
            return self.parent.content
        else:
            container = getattr(self.parent, self.location)
            if isinstance(container, (ListContainer, DictContainer)):
                return container
            else:
                assert self is container  # id(self) == id(container)

    def offset(self, n) -> 'Element':
        """
        Return a sibling element offset by n

        :rtype: :class:`Element` | ``None``
        """

        idx = self.index
        if idx is not None:
            sibling = idx + n
            container = self.container
            if 0 <= sibling < len(container):
                return container[sibling]

        return None

    @property
    def next(self):
        """
        Return the next sibling.
        Note that ``elem.offset(1) == elem.next``

        :rtype: :class:`Element` | ``None``

        """
        return self.offset(1)

    @property
    def prev(self):
        """
        Return the previous sibling.
        Note that ``elem.offset(-1) == elem.prev``

        :rtype: :class:`Element` | ``None``
        """
        return self.offset(-1)

    def ancestor(self, n):
        """
        Return the n-th ancestor.
        Note that ``elem.ancestor(1) == elem.parent``

        :rtype: :class:`Element` | ``None``
        """
        if not isinstance(n, int) or n < 1:
            raise TypeError('Ancestor needs to be positive, received', n)

        if n == 1 or self.parent is None:
            return self.parent
        else:
            return self.parent.ancestor(n-1)

    # ---------------------------
    # Walking
    # ---------------------------

    @property
    def doc(self):
        """
        Return the root Doc element (if there is one)
        """
        guess = self
        while guess is not None and guess.tag != 'Doc':
            guess = guess.parent  # If no parent, this will be None
        return guess  # Returns either Doc or None

    def walk(self, action, doc=None):
        """
        Walk through the element and all its children (sub-elements),
        applying the provided function ``action``.

        A trivial example would be:

        .. code-block:: python

            from panflute import *

            def no_action(elem, doc):
                pass

            doc = Doc(Para(Str('a')))
            altered = doc.walk(no_action)


        :param action: function that takes (element, doc) as arguments.
        :type action: :class:`function`
        :param doc: root document; used to access metadata,
            the output format (in ``.format``, other elements, and
            other variables). Only use this variable if for some reason
            you don't want to use the current document of an element.
        :type doc: :class:`.Doc`
        :rtype: :class:`Element` | ``[]`` | ``None``
        """

        # Infer the document thanks to .parent magic
        if doc is None:
            doc = self.doc

        # First iterate over children
        for child in self._children:
            obj = getattr(self, child)
            if obj is None:
                pass  # Empty table headers or captions

            elif hasattr(child, 'walk'):
                ans = obj.walk(action, doc)
                setattr(self, child, ans)

            else:
                raise TypeError(type(obj))

        # Then apply the action to the element
        altered = action(self, doc)

        return self if altered is None else altered


class Inline(Element):
    """
    Base class of all inline elements
    """
    __slots__ = ['_content']
    _children = ['content']
    # child_type = Inline

    def __init__(self, *args: List['Inline']):
        super(Inline, self).__init__()
        self._set_content(args, self.child_type)

    def _slots_to_json(self):
        return self.content.to_json()

Inline.child_type = Inline


class InlineText(Inline):

    __slots__ = ['text', 'format']
    _children = []
    default_format = None

    def __init__(self, text: str, format: str=None):
        super(Inline, self).__init__()
        if format is None:
            format = self.default_format

        self.text = check_type(text, str)
        self.format = check_group(format, RAW_FORMATS)

    def _slots_to_json(self):
        return [self.format, self.text]


class Block(Element):
    """
    Base class of all block elements
    """
    __slots__ = ['_content', 'identifier', 'classes', 'attributes']
    _children = ['content']
    child_type = Inline

    def __init__(self, *args, identifier: str='', classes: List[AnyStr]=None, attributes: Dict=None, **kwargs):
        super(Block, self).__init__(identifier=identifier)
        if classes is None:
            classes = []
        if attributes is None:
            attributes = {}

        self._set_ica(identifier, classes, attributes)
        self._set_content(args, self.child_type)

    def _slots_to_json(self):
        return self.content.to_json()


class BlockText(Block):

    __slots__ = ['text', 'format']
    _children = []

    def __init__(self, text: str, format: str='html'):
        super(BlockText, self).__init__()
        self.text = check_type(text, str)
        self.format = check_group(format, RAW_FORMATS)

    def _slots_to_json(self):
        return [self.format, self.text]


class InlineBlock(Inline, Block):
    """
    Base class of all inline block elements (e.g. Span)
    """
    __slots__ = ['_content', 'identifier', 'classes', 'attributes']
    _children = ['content']

    def __init__(self, *args: List[Inline], **kwargs):
        super(InlineBlock, self).__init__(**kwargs)
        self._set_content(args, Inline)


class MetaValue(Element):
    """
    Base class of all metadata elements
    """
    __slots__ = []
    _children =  []
