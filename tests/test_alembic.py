# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2021 TU Wien.
# Copyright (C) 2024 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test alembic recipes for Invenio-accounts."""

import pytest
from invenio_db.utils import alembic_test_context, drop_alembic_version_table


def test_alembic(app):
    """Test alembic recipes."""
    ext = app.extensions["invenio-db"]

    from invenio_db import db

    if db.engine.name == "sqlite":
        raise pytest.skip("Upgrades are not supported on SQLite.")

    app.config["ALEMBIC_CONTEXT"] = alembic_test_context()

    # Check that this package's SQLAlchemy models have been properly registered
    tables = [x for x in db.metadata.tables]
    assert "accounts_userrole" in tables
    assert "accounts_role" in tables
    assert "accounts_user" in tables

    # Check that Alembic agrees that there's no further tables to create.
    assert not ext.alembic.compare_metadata()

    # Drop everything and recreate tables all with Alembic
    db.drop_all()
    drop_alembic_version_table()
    ext.alembic.upgrade()
    assert not ext.alembic.compare_metadata()

    # Try to upgrade and downgrade
    ext.alembic.stamp()
    ext.alembic.downgrade(target="843bc79c426f")
    ext.alembic.upgrade()
    assert not ext.alembic.compare_metadata()

    drop_alembic_version_table()
