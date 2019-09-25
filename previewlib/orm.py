"""Object-relational mappings."""

from datetime import datetime, timedelta
from uuid import uuid4

from peewee import DateTimeField, FixedCharField, ForeignKeyField, UUIDField

from cmslib.orm.group import Group
from filedb import FileError, get
from his import CUSTOMER
from peeweeplus import JSONModel, MySQLDatabase
from terminallib import Deployment

from previewlib.config import CONFIG
from previewlib.messages import NO_SUCH_OBJECT, NO_SUCH_FILE, FILEDB_ERROR


__all__ = [
    'TOKEN_TYPES',
    'DeploymentPreviewToken',
    'GroupPreviewToken',
    'FileAccessToken'
]


DATABASE = MySQLDatabase.from_config(CONFIG['db'])


class _PreviewModel(JSONModel):
    """Common base model."""

    class Meta:     # pylint: disable=C0111,R0903
        database = DATABASE
        schema = database.database


class _PreviewToken(_PreviewModel):
    """Common abstract preview token."""

    token = UUIDField(default=uuid4)
    obj = None

    @classmethod
    def _get_rel_record(cls, ident):
        """Returns a related object by its ID."""
        model = cls.obj.rel_model
        condition = model.id == ident
        condition &= model.customer == CUSTOMER.id

        try:
            return model.get(condition)
        except model.DoesNotExist:
            raise NO_SUCH_OBJECT.update(type=model.__name__)

    @classmethod
    def generate(cls, ident, force=False):
        """Returns a token for the respective resource."""
        rel_record = cls._get_rel_record(ident)

        if force:
            return cls(obj=rel_record)

        try:
            return cls.get(cls.obj == rel_record)
        except cls.DoesNotExist:
            return cls(obj=rel_record)

    @classmethod
    def by_id(cls, ident):
        """Returns a token by its ID while checking the customer."""
        rel_model = cls.obj.rel_model
        condition = (cls.id == ident) & (rel_model.customer == CUSTOMER.id)
        return cls.join(rel_model).select().where(condition).get()

    @classmethod
    def for_customer(cls):
        """Returns a token by its ID while checking the customer."""
        return cls.join(cls.obj.rel_model).select().where(
            cls.obj.rel_model.customer == CUSTOMER.id)


class DeploymentPreviewToken(_PreviewToken):
    """Preview tokens for deployments."""

    class Meta:     # pylint: disable=C0111,R0903
        table_name = 'deployment_preview_token'

    obj = ForeignKeyField(
        Deployment, column_name='deployment', on_delete='CASCADE')


class GroupPreviewToken(_PreviewToken):
    """Preview tokens for groups."""

    class Meta:     # pylint: disable=C0111,R0903
        table_name = 'group_preview_token'

    obj = ForeignKeyField(Group, column_name='group', on_delete='CASCADE')


class FileAccessToken(_PreviewModel):
    """Temporary file access token."""

    VALIDITY = timedelta(minutes=5)

    class Meta:     # pylint: disable=C0111,R0903
        table_name = 'file_access_token'

    token = UUIDField()
    sha256sum = FixedCharField(64)
    valid_until = DateTimeField()
    requested_on = DateTimeField(null=True)

    @classmethod
    def from_sha256sum(cls, sha256sum, *, token=None, valid_until=None):
        """Adds entries for the respective
        SHA-256 checksum and returns the record.
        """
        token = token or uuid4()
        valid_until = valid_until or datetime.now() + cls.VALIDITY
        record = cls()
        record.token = token
        record.sha256sum = sha256sum
        record.valid_until = valid_until
        record.save()
        return record

    @classmethod
    def token_for_sha256sums(cls, sha256sums):
        """Adds entries for the respective SHA-256
        checksums and returns the token.
        """
        token = uuid4()
        valid_until = datetime.now() + cls.VALIDITY

        for sha256sum in sha256sums:
            cls.from_sha256sum(sha256sum, token=token, valid_until=valid_until)

        return token

    @classmethod
    def headers_for_sha256sums(cls, sha256sums):
        """Adds entries for respective SHA-256
        checksums and returns a response headers.
        """
        token = cls.token_for_sha256sums(sha256sums)
        return {'fileAccressToken': token.hex}

    @classmethod
    def headers_for_presentation(cls, presentation):
        """Returns a response headers for the
        respective presentation object.
        """
        sha256sums = {file.sha256sum for file in presentation.files}
        return cls.headers_for_sha256sums(sha256sums)

    @classmethod
    def request(cls, sha256sum, token):
        """Requests the file with the respective ID and token."""
        condition = (cls.sha256sum == sha256sum) & (cls.token == token)

        try:
            record = cls.get(condition)
        except cls.DoesNotExist:
            raise NO_SUCH_FILE

        now = datetime.now()

        if record.valid_until < now:
            raise NO_SUCH_FILE

        if record.requested_on is not None:
            raise NO_SUCH_FILE

        record.requested_on = now
        record.save()

        try:
            return get(record.sha256sum)
        except FileError:
            raise FILEDB_ERROR


TOKEN_TYPES = {
    'deployment': DeploymentPreviewToken,
    'group': GroupPreviewToken
}
