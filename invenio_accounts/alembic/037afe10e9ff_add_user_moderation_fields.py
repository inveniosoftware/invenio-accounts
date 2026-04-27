#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add user moderation fields."""

from alembic import op
from sqlalchemy import Column, DateTime

# revision identifiers, used by Alembic.
revision = "037afe10e9ff"
down_revision = "f2522cdd5fcd"
branch_labels = ()
depends_on = ""


def upgrade():
    """Upgrade database."""
    users_tbl = "accounts_user"

    # create the new columns as nullable fields
    op.add_column(users_tbl, Column("blocked_at", DateTime(), nullable=True))
    op.add_column(users_tbl, Column("verified_at", DateTime(), nullable=True))


def downgrade():
    """Downgrade database."""
    users_tbl = "accounts_user"
    op.drop_column(users_tbl, "blocked_at")
    op.drop_column(users_tbl, "verified_at")
