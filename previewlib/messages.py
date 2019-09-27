"""Preview related WSGI JSON messages."""

from wsgilib import JSONMessage


__all__ = [
    'UNAUTHORIZED',
    'INVALID_TOKEN_TYPE',
    'NO_SUCH_OBJECT',
    'MISSING_TOKEN_TYPE',
    'MISSING_IDENTIFIER',
    'NO_SUCH_TOKEN',
    'TOKEN_DELETED',
    'FILEDB_ERROR'
]


UNAUTHORIZED = JSONMessage('Preview not allowed.', status=401)
INVALID_TOKEN_TYPE = JSONMessage('Invalid token type.', status=400)
NO_SUCH_OBJECT = JSONMessage('No such preview object.', status=404)
MISSING_TOKEN_TYPE = JSONMessage('Missing token type.', status=400)
MISSING_IDENTIFIER = JSONMessage('Missing identifier.', status=400)
NO_SUCH_TOKEN = JSONMessage('No such token.', status=404)
TOKEN_DELETED = JSONMessage('No such token.', status=200)
FILEDB_ERROR = JSONMessage('Error file filedb.', status=500)
