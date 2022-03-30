# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Module tests."""

from click.testing import CliRunner

from invenio_accounts.cli import roles_add, roles_create, roles_remove, \
    users_activate, users_create, users_deactivate


def test_cli_createuser(app):
    """Test create user CLI."""
    runner = app.test_cli_runner()

    # Missing params
    result = runner.invoke(
        users_create, input='1234\n1234\n')
    assert result.exit_code != 0

    # Create user with invalid email
    result = runner.invoke(
        users_create,
        ['not-an-email', '--password', '123456']
    )
    assert result.exit_code == 2

    # Create user
    result = runner.invoke(
        users_create,
        ['info@inveniosoftware.org', '--password', '123456']
    )
    assert result.exit_code == 0


def test_cli_createrole(app):
    """Test create user CLI."""
    runner = app.test_cli_runner()

    # Missing params
    result = runner.invoke(
        roles_create, ['-d', 'Test description'])
    assert result.exit_code != 0

    # Create role
    result = runner.invoke(
        roles_create,
        ['superusers', '-d', 'Test description'])
    assert result.exit_code == 0


def test_cli_addremove_role(app):
    """Test add/remove role."""
    runner = app.test_cli_runner()

    # Create a user and a role
    result = runner.invoke(
        users_create,
        ['a@example.org', '--password', '123456']
    )
    assert result.exit_code == 0
    result = runner.invoke(roles_create, ['superuser'])
    assert result.exit_code == 0

    # User not found
    result = runner.invoke(
        roles_add, ['inval@example.org', 'superuser'])
    assert result.exit_code != 0

    # Add:
    result = runner.invoke(
        roles_add, ['a@example.org', 'invalid'])
    assert result.exit_code != 0

    result = runner.invoke(
        roles_remove, ['inval@example.org', 'superuser'])
    assert result.exit_code != 0

    # Remove:
    result = runner.invoke(
        roles_remove, ['a@example.org', 'invalid'])
    assert result.exit_code != 0

    result = runner.invoke(
        roles_remove, ['b@example.org', 'superuser'])
    assert result.exit_code != 0

    result = runner.invoke(
        roles_remove, ['a@example.org', 'superuser'])
    assert result.exit_code != 0

    # Add:
    result = runner.invoke(roles_add,
                           ['a@example.org', 'superuser'])
    assert result.exit_code == 0
    result = runner.invoke(
        roles_add,
        ['a@example.org', 'superuser'])
    assert result.exit_code != 0

    # Remove:
    result = runner.invoke(
        roles_remove, ['a@example.org', 'superuser'])
    assert result.exit_code == 0


def test_cli_activate_deactivate(app):
    """Test create user CLI."""
    runner = app.test_cli_runner()

    # Create a user
    result = runner.invoke(
        users_create,
        ['a@example.org', '--password', '123456']
    )
    assert result.exit_code == 0

    # Activate
    result = runner.invoke(users_activate, ['in@valid.org'])
    assert result.exit_code != 0
    result = runner.invoke(users_deactivate, ['in@valid.org'])
    assert result.exit_code != 0

    result = runner.invoke(users_activate, ['a@example.org'])
    assert result.exit_code == 0
    result = runner.invoke(users_activate, ['a@example.org'])
    assert result.exit_code == 0

    # Deactivate
    result = runner.invoke(users_deactivate, ['a@example.org'])
    assert result.exit_code == 0
    result = runner.invoke(users_deactivate, ['a@example.org'])
    assert result.exit_code == 0
