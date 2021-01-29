"""Common preview functions."""

from typing import Union

from cmslib import Presentation
from wsgilib import ACCEPT, JSON, JSONMessage, XML

from previewlib.orm import FileAccessToken


__all__ = ['Response', 'make_response']


Response = Union[JSON, JSONMessage, XML]


def make_response(presentation: Presentation) -> Response:
    """Creates a response for the respective presentation."""

    file_preview_token = FileAccessToken.token_for_presentation(presentation)

    if 'application/xml' in ACCEPT or '*/*' in ACCEPT:
        presentation = presentation.to_dom()
        presentation.file_preview_token = file_preview_token.hex
        return XML(presentation)

    if 'application/json' in ACCEPT:
        json = presentation.to_json()
        json['filePreviewToken'] = file_preview_token.hex
        return JSON(json)

    return JSONMessage('Invalid content type.', status=400)
