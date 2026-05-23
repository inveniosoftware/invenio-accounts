# SPDX-FileCopyrightText: 2017-2018 CERN.
# SPDX-License-Identifier: MIT

"""Add new columns on SessionActivity."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e12419831262"
down_revision = "9848d0149abd"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    with op.batch_alter_table("accounts_user_session_activity") as batch_op:
        batch_op.add_column(sa.Column("browser", sa.String(80), nullable=True))
        batch_op.add_column(sa.Column("browser_version", sa.String(30), nullable=True))
        batch_op.add_column(sa.Column("country", sa.String(3), nullable=True))
        batch_op.add_column(sa.Column("device", sa.String(80), nullable=True))
        batch_op.add_column(sa.Column("ip", sa.String(80), nullable=True))
        batch_op.add_column(sa.Column("os", sa.String(80), nullable=True))


def downgrade():
    """Downgrade database."""
    with op.batch_alter_table("accounts_user_session_activity") as batch_op:
        batch_op.drop_column("os")
        batch_op.drop_column("ip")
        batch_op.drop_column("device")
        batch_op.drop_column("country")
        batch_op.drop_column("browser_version")
        batch_op.drop_column("browser")
