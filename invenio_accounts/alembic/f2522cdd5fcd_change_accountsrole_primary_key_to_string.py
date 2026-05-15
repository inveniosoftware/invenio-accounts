#
# This file is part of Invenio.
# Copyright (C) 2023 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Change AccountsRole primary key to string."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text
from sqlalchemy_utils import get_referencing_foreign_keys

from invenio_accounts.models import Role

# Invenio-Access depends on this package. During the evolution of these
# packages, the `AccountsRole` primary key changed from an integer to a string.
# Because `invenio-access` defines relationships against this model, the
# migration order must be linearized: some `invenio-access` revisions must run
# before this change, and others must run after it.
#
# To enforce that ordering, this migration conditionally depends on
# `invenio-access`. This creates an Alembic-level circular dependency between
# the two packages, so we handle it carefully: if `invenio-access` is
# installed, we force the correct linearization; otherwise, we depend only on
# the revision that introduces the primary-key change. This allows migrations
# to be tested in isolation.
#
# We cannot put this logic in `invenio_access` package. Alembic migration files
# are not regular importable modules from `.ext`, because the `alembic` directory
# is not a Python package (no __init__.py). For that reason, the dependency is
# resolved here and, when those packages are installed, their relevant migration
# revisions are added to `resolved_depends_on`.

resolved_depends_on = []
try:
    import invenio_communities

    # invenio_communities/alembic/37b21951084c_update_role_id_type_downgrade.py
    resolved_depends_on += ["37b21951084c"]

except ImportError:
    pass

try:
    import invenio_access

    # invenio_access/alembic/842a62b56e60_change_fk_accountsrole_to_string_downgrade.py
    resolved_depends_on += ["842a62b56e60"]

except ImportError:
    pass

# revision identifiers, used by Alembic.
revision = "f2522cdd5fcd"
down_revision = "eb9743315a9d"
branch_labels = ()
depends_on = resolved_depends_on


def upgrade():
    """Upgrade database."""
    # Drop primary key and all foreign keys
    ctx = op.get_context()
    if ctx.connection.engine.name == "mysql":
        # mysql does not support CASCADE on drop constraint command
        dependent_tables = get_referencing_foreign_keys(Role)

        for fk in dependent_tables:
            op.drop_constraint(
                fk.constraint.name, fk.constraint.table.name, type_="foreignkey"
            )

        op.execute(text("ALTER TABLE accounts_role MODIFY COLUMN id INT"))

        op.drop_constraint("pk_accounts_role", "accounts_role", type_="primary")
    else:
        # note: CASCADE here is what drops the foreign key constrains that reference `accounts_role`
        op.execute(
            text("ALTER TABLE accounts_role DROP CONSTRAINT pk_accounts_role CASCADE;")
        )

    op.alter_column(
        "accounts_userrole",
        "role_id",
        existing_type=sa.Integer,
        type_=sa.String(80),
        postgresql_using="role_id::integer",
    )
    # Change primary key type
    # server_default=None will remove the autoincrement
    op.alter_column(
        "accounts_role",
        "id",
        existing_type=sa.Integer,
        type_=sa.String(80),
        server_default=None,
    )
    op.create_primary_key("pk_accounts_role", "accounts_role", ["id"])
    # Add new column `is_managed`
    op.add_column(
        "accounts_role",
        sa.Column(
            "is_managed", sa.Boolean(name="is_managed"), default=True, nullable=True
        ),
    )
    op.execute(text("UPDATE accounts_role SET is_managed = true;"))
    op.alter_column(
        "accounts_role", "is_managed", existing_type=sa.Boolean, nullable=False
    )

    # Re-create the foreign key constraint
    op.create_foreign_key(
        "fk_accounts_userrole_role_id",
        "accounts_userrole",
        "accounts_role",
        ["role_id"],
        ["id"],
    )


def downgrade():
    """Downgrade database."""
    # Drop new column `is_managed`
    op.drop_column("accounts_role", "is_managed")
    ctx = op.get_context()
    if ctx.connection.engine.name == "mysql":
        # mysql does not support CASCADE on drop constraint command
        dependent_tables = get_referencing_foreign_keys(Role)

        for fk in dependent_tables:
            op.drop_constraint(
                fk.constraint.name, fk.constraint.table.name, type_="foreignkey"
            )

        op.drop_constraint("pk_accounts_role", "accounts_role", type_="primary")
    else:
        op.execute(
            text("ALTER TABLE accounts_role DROP CONSTRAINT pk_accounts_role CASCADE;")
        )

    op.alter_column(
        "accounts_userrole",
        "role_id",
        existing_type=sa.String(80),
        type_=sa.Integer,
        postgresql_using="role_id::integer",
    )
    # Change primary key type
    # op.drop_constraint("pk_accounts_role", "accounts_role", type_="primary")
    op.alter_column(
        "accounts_role",
        "id",
        existing_type=sa.String(80),
        type_=sa.Integer,
        postgresql_using="id::integer",
    )
    op.create_primary_key("pk_accounts_role", "accounts_role", ["id"])
    op.alter_column(
        "accounts_role",
        "id",
        existing_type=sa.String(80),
        type_=sa.Integer,
        autoincrement=True,
        existing_autoincrement=True,
        nullable=False,
    )

    # Re-create the foreign key constraint
    op.create_foreign_key(
        "fk_accounts_userrole_role_id",
        "accounts_userrole",
        "accounts_role",
        ["role_id"],
        ["id"],
    )
