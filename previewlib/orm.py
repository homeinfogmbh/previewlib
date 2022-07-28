"""Object-relational mappings."""

from __future__ import annotations
from datetime import datetime, timedelta
from logging import getLogger
from typing import Any, Iterable, Optional, Union
from uuid import UUID, uuid4

from peewee import DateTimeField
from peewee import FixedCharField
from peewee import ForeignKeyField
from peewee import ModelSelect
from peewee import UUIDField

from cmslib import Group
from filedb import File
from hwdb import Deployment
from mdb import Customer
from peeweeplus import JSONModel, MySQLDatabaseProxy

from previewlib.messages import FILEDB_ERROR, NO_SUCH_OBJECT, UNAUTHORIZED


__all__ = [
    'TOKEN_TYPES',
    'PreviewToken',
    'DeploymentPreviewToken',
    'GroupPreviewToken',
    'FileAccessToken'
]


DATABASE = MySQLDatabaseProxy('previewlib')
LOGGER = getLogger('previewlib')


class PreviewModel(JSONModel):
    """Common base model."""

    class Meta:
        database = DATABASE
        schema = database.database


class PreviewToken(PreviewModel):
    """Common abstract preview token."""

    token = UUIDField(default=uuid4)
    obj = None

    @classmethod
    def _get_rel_record(
            cls,
            ident: int,
            customer: Union[Customer, int]
    ) -> PreviewToken:
        """Returns a related object by its ID."""
        model = cls.obj.rel_model
        condition = model.id == ident
        condition &= model.customer == customer

        try:
            return model.get(condition)
        except model.DoesNotExist:
            raise NO_SUCH_OBJECT.update(type=model.__name__) from None

    @classmethod
    def generate(
            cls,
            ident: int,
            customer: Union[Customer, int],
            *,
            force: bool = False
    ) -> PreviewToken:
        """Returns a token for the respective resource."""
        rel_record = cls._get_rel_record(ident, customer)

        if force:
            return cls(obj=rel_record)

        try:
            return cls.get(cls.obj == rel_record)
        except cls.DoesNotExist:
            return cls(obj=rel_record)

    @classmethod
    def by_id(cls, ident: int, customer: Union[Customer, int]) -> PreviewToken:
        """Returns a token by its ID while checking the customer."""
        rel_model = cls.obj.rel_model
        condition = (cls.id == ident) & (rel_model.customer == customer)
        return cls.join(rel_model).select().where(condition).get()

    @classmethod
    def for_customer(cls, customer: Union[Customer, int]) -> ModelSelect:
        """Returns a token by its ID while checking the customer."""
        rel_model = cls.obj.rel_model
        condition = rel_model.customer == customer
        return cls.join(rel_model).select().where(condition)


class DeploymentPreviewToken(PreviewToken):
    """Preview tokens for deployments."""

    class Meta:
        table_name = 'deployment_preview_token'

    obj = ForeignKeyField(
        Deployment, column_name='deployment', on_delete='CASCADE'
    )


class GroupPreviewToken(PreviewToken):
    """Preview tokens for groups."""

    class Meta:
        table_name = 'group_preview_token'

    obj = ForeignKeyField(Group, column_name='group', on_delete='CASCADE')


class FileAccessToken(PreviewModel):
    """Temporary file access token."""

    VALIDITY = timedelta(minutes=5)

    class Meta:
        table_name = 'file_access_token'

    token = UUIDField()
    sha256sum = FixedCharField(64)
    valid_until = DateTimeField()
    requested_on = DateTimeField(null=True)

    @classmethod
    def clean_expired(cls) -> None:
        """Deletes expired records."""
        for record in cls.select().where(cls.valid_until < datetime.now()):
            record.delete_instance()

    @classmethod
    def from_sha256sum(
            cls,
            sha256sum: str,
            *,
            token: Optional[UUID] = None,
            valid_until: Optional[datetime] = None
    ) -> FileAccessToken:
        """Adds entries for the respective
        SHA-256 checksum and returns the record.
        """
        cls.clean_expired()
        valid_until = valid_until or datetime.now() + cls.VALIDITY
        record = cls()
        record.token = token or uuid4()
        record.sha256sum = sha256sum
        record.valid_until = valid_until
        record.save()
        return record

    @classmethod
    def token_for_sha256sums(cls, sha256sums: Iterable[str]) -> UUID:
        """Adds entries for the respective SHA-256
        checksums and returns the token.
        """
        token = uuid4()
        valid_until = datetime.now() + cls.VALIDITY

        for sha256sum in sha256sums:
            cls.from_sha256sum(sha256sum, token=token, valid_until=valid_until)

        return token

    @classmethod
    def token_for_presentation(cls, presentation: Any) -> UUID:
        """Returns a response headers for the
        respective presentation object.
        """
        sha256sums = set()

        for file in presentation.files:
            sha256sums.add(file.sha256sum)

        return cls.token_for_sha256sums(sha256sums)

    @classmethod
    def request(cls, token: UUID, sha256sum: str) -> File:
        """Requests the file with the respective ID and token."""
        cls.clean_expired()
        condition = (cls.token == token) & (cls.sha256sum == sha256sum)

        try:
            record = cls.get(condition)
        except cls.DoesNotExist:
            raise UNAUTHORIZED from None

        now = datetime.now()

        if record.valid_until < now:
            raise UNAUTHORIZED from None

        try:
            return File.by_sha256sum(record.sha256sum)
        except File.DoesNotExist:
            raise FILEDB_ERROR from None


TOKEN_TYPES = {
    'deployment': DeploymentPreviewToken,
    'group': GroupPreviewToken
}
