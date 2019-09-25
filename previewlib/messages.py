"""Preview related WSGI JSON messages."""

from wsgilib import JSONMessage


__all__ = ['UNAUTHORIZED', 'INVALID_TOKEN_TYPE', 'NO_SUCH_OBJECT']


UNAUTHORIZED = JSONMessage('Preview not allowed.', status=401)
INVALID_TOKEN_TYPE = JSONMessage('Invalid token type.', status=400)
NO_SUCH_OBJECT = JSONMessage('No such preview object.', status=404)
