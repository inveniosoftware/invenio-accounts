#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add unique constraint to domain category label."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1748440134"
down_revision = "6ec5ce377ca3"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # Add unique constraint to domain category label column
    # Note: This will fail if there are duplicate labels in the table
    # Clean up duplicates before running this migration if needed
    op.create_unique_constraint(
        "uq_accounts_domain_category_label", "accounts_domain_category", ["label"]
    )


def downgrade():
    """Downgrade database."""
    # Remove the unique constraint from domain category label column
    op.drop_constraint(
        "uq_accounts_domain_category_label", "accounts_domain_category", type_="unique"
    )
