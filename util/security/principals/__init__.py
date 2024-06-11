from functools import partial
from collections import namedtuple


Need = namedtuple('Need', ['method', 'value'])
"""A required need

This is just a named tuple, and practically any tuple will do.

The ``method`` attribute can be used to look up element 0, and the ``value``
attribute can be used to look up element 1.
"""


UserNeed = partial(Need, 'id')
UserNeed.__doc__ = """A need with the method preset to `"id"`."""


RoleNeed = partial(Need, 'role')
RoleNeed.__doc__ = """A need with the method preset to `"role"`."""


TypeNeed = partial(Need, 'type')
TypeNeed.__doc__ = """A need with the method preset to `"type"`."""


ActionNeed = partial(Need, 'action')
ActionNeed.__doc__ = """A need with the method preset to `"action"`."""


ItemNeed = namedtuple('ItemNeed', ['method', 'value', 'type'])
"""A required item need

An item need is just a named tuple, and practically any tuple will do. In
addition to other Needs, there is a type, for example this could be specified
as::

    ItemNeed('update', 27, 'posts')
    ('update', 27, 'posts') # or like this

And that might describe the permission to update a particular blog post. In
reality, the developer is free to choose whatever convention the permissions
are.
"""

class PermissionDenied(RuntimeError):
    """Permission denied to the resource"""
    
    