#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
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

"""Add new columns on SessionActivity."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e12419831262'
down_revision = '9848d0149abd'
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    with op.batch_alter_table('accounts_user_session_activity') as batch_op:
        batch_op.add_column(sa.Column('browser', sa.String(80), nullable=True))
        batch_op.add_column(
            sa.Column('browser_version', sa.String(30), nullable=True))
        batch_op.add_column(
            sa.Column('country', sa.String(3), nullable=True))
        batch_op.add_column(
            sa.Column('device', sa.String(80), nullable=True))
        batch_op.add_column(
            sa.Column('ip', sa.String(80), nullable=True))
        batch_op.add_column(
            sa.Column('os', sa.String(80), nullable=True))


def downgrade():
    """Downgrade database."""
    with op.batch_alter_table('accounts_user_session_activity') as batch_op:
        batch_op.drop_column('os')
        batch_op.drop_column('ip')
        batch_op.drop_column('device')
        batch_op.drop_column('country')
        batch_op.drop_column('browser_version')
        batch_op.drop_column('browser')
