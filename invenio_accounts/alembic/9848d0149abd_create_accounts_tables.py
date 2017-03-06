# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Create accounts tables."""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '9848d0149abd'
down_revision = '843bc79c426f'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.create_table(
        'accounts_role',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=80), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_table(
        'accounts_user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('password', sa.String(length=255), nullable=True),
        sa.Column('active', sa.Boolean(name='active'), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('current_login_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_ip',
                  sqlalchemy_utils.types.ip_address.IPAddressType(),
                  nullable=True),
        sa.Column('current_login_ip',
                  sqlalchemy_utils.types.ip_address.IPAddressType(),
                  nullable=True),
        sa.Column('login_count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_table(
        'accounts_user_session_activity',
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('updated', sa.DateTime(), nullable=False),
        sa.Column('sid_s', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ['user_id'], [u'accounts_user.id'],
            name='fk_accounts_session_activity_user_id',
        ),
        sa.PrimaryKeyConstraint('sid_s')
    )
    op.create_table(
        'accounts_userrole',
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('role_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ['role_id'], ['accounts_role.id'],
            name='fk_accounts_userrole_role_id',
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['accounts_user.id'],
            name='fk_accounts_userrole_user_id',
        ),
    )
    with op.batch_alter_table('transaction') as batch_op:
        batch_op.add_column(sa.Column(
            'user_id',
            sa.Integer(),
            sa.ForeignKey(
                'accounts_user.id', name='fk_transaction_accounts_user_id'),
            nullable=True,
        ))
        batch_op.create_index(
            op.f('ix_transaction_user_id'), ['user_id'], unique=False
        )


def downgrade():
    """Downgrade database."""
    ctx = op.get_context()
    insp = Inspector.from_engine(ctx.connection.engine)

    for fk in insp.get_foreign_keys('transaction'):
        if fk['referred_table'] == 'accounts_user':
            op.drop_constraint(
                op.f(fk['name']), 'transaction', type_='foreignkey'
            )

    with op.batch_alter_table('transaction') as batch_op:
        batch_op.drop_index(op.f('ix_transaction_user_id'))
        batch_op.drop_column('user_id')
    op.drop_table('accounts_userrole')
    op.drop_table('accounts_user_session_activity')
    op.drop_table('accounts_user')
    op.drop_table('accounts_role')
