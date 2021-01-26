"""WSGI interface."""

from typing import Union
from uuid import UUID

from flask import request

from his import authenticated, authorized, Application
from hwdb import Deployment, SmartTV
from wsgilib import Binary, JSON, JSONMessage

from previewlib.messages import UNAUTHORIZED
from previewlib.messages import INVALID_TOKEN_TYPE
from previewlib.messages import MISSING_TOKEN_TYPE
from previewlib.messages import MISSING_IDENTIFIER
from previewlib.messages import NO_SUCH_TOKEN
from previewlib.messages import TOKEN_DELETED
from previewlib.orm import TOKEN_TYPES, DeploymentPreviewToken, FileAccessToken


__all__ = ['APPLICATION']


APPLICATION = Application('preview')


@authenticated
@authorized('preview')
def list_(type) -> Union[JSON, JSONMessage]:    # pylint: disable=W0622
    """Lists the customer's preview tokens."""

    try:
        token_class = TOKEN_TYPES[type]
    except KeyError:
        return INVALID_TOKEN_TYPE

    return JSON([token.to_json() for token in token_class.for_customer()])


@authenticated
@authorized('preview')
def generate() -> Union[JSON, JSONMessage]:
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
def delete(type, ident) -> JSONMessage:     # pylint: disable=W0622
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


def get_file(sha256sum) -> Binary:
    """Returns a deployment-related file."""

    try:
        token = UUID(request.args['token'])
    except (KeyError, ValueError):
        return UNAUTHORIZED

    file = FileAccessToken.request(token, sha256sum)

    if 'stream' in request.args:
        return file.stream()

    return Binary(file.bytes)


def generate_for_smart_tv() -> Union[JSON, JSONMessage]:
    """Generates a deployment preview token for a legacy E-TV."""

    try:
        customer = request.json['customer']
    except KeyError:
        return JSONMessage('No customer specified.', status=400)

    try:
        ident = request.json['id']
    except KeyError:
        return JSONMessage('No ID specified.', status=400)

    condition = (Deployment.customer == customer) & (SmartTV.id == ident)

    try:
        smart_tv = SmartTV.select(cascade=True).where(condition).get()
    except SmartTV.DoesNotExist:
        return JSONMessage('No such SmartTV.', status=404)

    token = DeploymentPreviewToken.generate(smart_tv.deployment.id)
    token.save()
    return JSON({'token': token.token.hex})


APPLICATION.add_routes((
    ('GET', '/token/<type>', list_),
    ('POST', '/token', generate),
    ('DELETE', '/token/<type>/<int:ident>', delete),
    ('GET', '/file/<sha256sum>', get_file),
    ('POST', '/smarttv', generate_for_smart_tv)
))
