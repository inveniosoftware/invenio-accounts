#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add user moderation fields."""

from alembic import op
from sqlalchemy import Column, DateTime

# Invenio-Access depends on this package. During the evolution of this package,
# the AccountsRole primary key was changed from an integer to a string. Because
# invenio-access used this model in relationship definitions, the Alembic history
# must be serialized so that some invenio-access migrations run before this change
# and others run after it.
#
# The only way to do this is to make this package depend on invenio-access,
# which creates a circular dependency at the Alembic level between the two
# packages. To allow package migrations to be tested in isolation, we use this
# switch: if invenio-access is installed, force the correct linearization; if
# not, depend only on the primary-key-change revision.
try:
    import invenio_access

    resolved_down_revision = "f9843093f686"

except ImportError:
    resolved_down_revision = "f2522cdd5fcd"


# revision identifiers, used by Alembic.
revision = "037afe10e9ff"
down_revision = resolved_down_revision
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
