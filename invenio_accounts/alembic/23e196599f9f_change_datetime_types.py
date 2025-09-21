#
# This file is part of Invenio.
# Copyright (C) 2016-2024 CERN.
# Copyright (C) 2026 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Alter datetime columns to utc aware datetime columns."""

from invenio_db.utils import (
    update_table_columns_column_type_to_datetime,
    update_table_columns_column_type_to_utc_datetime,
)

# revision identifiers, used by Alembic.
revision = "23e196599f9f"
down_revision = "6ec5ce377ca3"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    for table_name in [
        "accounts_role",
        "accounts_user",
        "accounts_user_session_activity",
        "accounts_useridentity",
        "accounts_domains",
    ]:
        update_table_columns_column_type_to_utc_datetime(table_name, "created")
        update_table_columns_column_type_to_utc_datetime(table_name, "updated")

    update_table_columns_column_type_to_utc_datetime("accounts_user", "confirmed_at")
    update_table_columns_column_type_to_utc_datetime("accounts_user", "blocked_at")
    update_table_columns_column_type_to_utc_datetime("accounts_user", "verified_at")
    update_table_columns_column_type_to_utc_datetime(
        "accounts_user_login_information", "last_login_at"
    )
    update_table_columns_column_type_to_utc_datetime(
        "accounts_user_login_information", "current_login_at"
    )


def downgrade():
    """Downgrade database."""
    for table_name in [
        "accounts_role",
        "accounts_user",
        "accounts_user_session_activity",
        "accounts_useridentity",
        "accounts_domains",
    ]:
        update_table_columns_column_type_to_datetime(table_name, "created")
        update_table_columns_column_type_to_datetime(table_name, "updated")

    update_table_columns_column_type_to_datetime("accounts_user", "confirmed_at")
    update_table_columns_column_type_to_datetime("accounts_user", "blocked_at")
    update_table_columns_column_type_to_datetime("accounts_user", "verified_at")
    update_table_columns_column_type_to_datetime(
        "accounts_user_login_information", "last_login_at"
    )
    update_table_columns_column_type_to_datetime(
        "accounts_user_login_information", "current_login_at"
    )
