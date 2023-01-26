#
# This file is part of Invenio.
# Copyright (C) 2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Change AccountsRole primary key to string."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8f11b75e0995'
down_revision = 'eb9743315a9d'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # Drop foreign key and change type
    op.drop_constraint("fk_accounts_userrole_role_id", "accounts_userrole", type_="foreignkey")
    op.alter_column('accounts_userrole', 'role_id', existing_type=sa.Integer, type_=sa.String(80))
    # Change primary key type
    op.drop_constraint('pk_accounts_role', 'accounts_role', type_='primary')
    # server_default=None will remove the autoincrement
    op.alter_column('accounts_role', 'id', existing_type=sa.Integer, type_=sa.String(80), server_default=None)
    op.execute('DROP SEQUENCE accounts_role_id_seq')
    op.create_primary_key('pk_accounts_role', 'accounts_role', ['id'])
    # Add new column `is_managed`
    op.add_column('accounts_role', sa.Column('is_managed', sa.Boolean(name='is_managed'), default=True, nullable=False))
    # Re-create the foreign key constraint
    op.create_foreign_key('fk_accounts_userrole_role_id', 'accounts_userrole', 'accounts_role', ['role_id'], ['id'])


def downgrade():
    """Downgrade database."""
    # Drop foreign key and change type
    op.drop_constraint("fk_accounts_userrole_role_id", "accounts_userrole", type_="foreignkey")
    op.alter_column('accounts_userrole', 'role_id', existing_type=sa.String(80), type_=sa.Integer)
    # Change primary key type
    op.drop_constraint('pk_accounts_role', 'accounts_role', type_='primary')
    op.alter_column('accounts_role', 'id', existing_type=sa.String(80), type_=sa.Integer)
    op.create_primary_key('pk_accounts_role', 'accounts_role', ['id'])
    op.alter_column('accounts_role', 'id', existing_type=sa.Integer, autoincrement=True, existing_autoincrement=True, nullable=False)
    # Drop new column `is_managed`
    op.drop_column('accounts_role', 'is_managed')
    # Re-create the foreign key constraint
    op.create_foreign_key('fk_accounts_userrole_role_id', 'accounts_userrole', 'accounts_role', ['role_id'], ['id'])

