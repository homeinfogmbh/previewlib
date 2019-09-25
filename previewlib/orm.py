"""Object-relational mappings."""

from uuid import uuid4

from peewee import ForeignKeyField, UUIDField

from cmslib.orm.group import Group
from his import CUSTOMER
from peeweeplus import JSONModel, MySQLDatabase
from terminallib import Deployment

from previewlib.config import CONFIG
from previewlib.messages import NO_SUCH_OBJECT


__all__ = ['TOKEN_TYPES', 'GroupPreviewToken']


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
    def generate(cls, ident, force=False):
        """Returns a token for the respective resource."""
        model = cls.obj.rel_model

        try:
            record = model.get(
                (model.id == ident) & (model.customer == CUSTOMER.id))
        except model.DoesNotExist:
            raise NO_SUCH_OBJECT.update(type=model.__name__)

        if force:
            return cls(obj=record)

        try:
            return cls.get(cls.obj == record)
        except cls.DoesNotExist:
            return cls(obj=record)


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


MODELS = (DeploymentPreviewToken, GroupPreviewToken)
TOKEN_TYPES = {
    'deployment': DeploymentPreviewToken,
    'group': GroupPreviewToken
}
