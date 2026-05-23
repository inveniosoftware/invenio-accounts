# SPDX-FileCopyrightText: 2022 CERN.
# SPDX-License-Identifier: MIT

"""Create UserIdentity table."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "62efc52773d4"
down_revision = "dfbdf43a3e96"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.create_table(
        "accounts_useridentity",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("method", sa.String(length=255), nullable=False),
        sa.Column("id_user", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["id_user"],
            ["accounts_user.id"],
            name=op.f("fk_accounts_useridentity_id_user_accounts_user"),
        ),
        sa.PrimaryKeyConstraint("id", "method", name=op.f("pk_accounts_useridentity")),
    )
    op.create_index(
        "accounts_useridentity_id_user_method",
        "accounts_useridentity",
        ["id_user", "method"],
        unique=True,
    )


def downgrade():
    """Downgrade database."""
    op.drop_table("accounts_useridentity")
