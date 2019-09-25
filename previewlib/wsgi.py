"""WSGI interface."""

from flask import request

from cmslib.messages.preview import INVALID_TOKEN_TYPE
from cmslib.orm.preview import TOKEN_TYPES
from his import authenticated, authorized
from wsgilib import JSON


__all__ = ['ROUTES']


@authenticated
@authorized('preview')
def generate():
    """Generates a preview token of the
    specified type for the provided ID.
    """

    type_ = request.json.get('type')

    if not type_:
        return MISSING_TOKEN_TYPE

    ident = request.json.get('id')

    if not ident:
        return MISSING_IDENTIFIER
    
    try:
        token_class = TOKEN_TYPES[type_]
    except KeyError:
        return INVALID_TOKEN_TYPE

    force = request.json.get('force', False)
    token = token_class.generate(ident, force=force)
    token.save()
    return JSON({'token': token.token.hex})


@authenticated
@authorized('preview')
def delete(type, ident):
    """Deletes a preview token."""
    
    try:
        token_class = TOKEN_TYPES[type]
    except KeyError:
        return INVALID_TOKEN_TYPE

    try:
        token = token_class.by_id(ident)
    except token_class.DoesNotExist:
        return NO_SUCH_TOKEN

    token.delete_instance()
    return TOKEN_DELETED


APPLICATION.add_routes((
    ('POST', '/token', generate),
    ('GET', '/token/<type>/<int:ident>', delete)
))