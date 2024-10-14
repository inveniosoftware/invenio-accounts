# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2023 CERN.
# Copyright (C) 2024 Graz University of Technology.
# Copyright (C) 2024 KTH Royal Institute of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Command Line Interface for accounts."""

import json
from datetime import datetime
from functools import wraps

import click
from flask import current_app
from flask.cli import with_appcontext
from flask_security.forms import ConfirmRegisterForm
from flask_security.utils import hash_password
from invenio_db import db
from werkzeug.datastructures import MultiDict
from werkzeug.local import LocalProxy

from .models import DomainCategory

_datastore = LocalProxy(lambda: current_app.extensions["security"].datastore)


def commit(fn):
    """Commit changes in datastore (used as a decorator)."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        fn(*args, **kwargs)
        _datastore.commit()

    return wrapper


@click.group()
def users():
    """User commands."""


@click.group()
def roles():
    """Role commands."""


@click.group()
def domains():
    """Domain commands."""


@users.command("create")
@click.argument("email")
@click.password_option()
@click.option("-a", "--active", default=False, is_flag=True)
@click.option("-c", "--confirm", default=False, is_flag=True)
@click.option("-p", "--profile")
@with_appcontext
@commit
def users_create(email, password, active, confirm, profile):
    """Create a user."""
    kwargs = dict(email=email, password=password, active="y" if active else "")

    form = ConfirmRegisterForm(MultiDict(kwargs), meta={"csrf": False})

    if form.validate():
        kwargs["password"] = hash_password(kwargs["password"])
        kwargs["active"] = active
        if confirm:
            kwargs["confirmed_at"] = datetime.utcnow()
        if profile:
            kwargs["user_profile"] = json.loads(profile)
        _datastore.create_user(**kwargs)
        click.secho("User created successfully.", fg="green")
        kwargs["password"] = "****"
        click.echo(kwargs)
    else:
        raise click.UsageError("Error creating user. %s" % form.errors)


@roles.command("create")
@click.argument("name")
@click.option("-d", "--description", default=None)
@with_appcontext
@commit
def roles_create(**kwargs):
    """Create a role."""
    _datastore.create_role(id=kwargs["name"], **kwargs)
    click.secho('Role "%(name)s" created successfully.' % kwargs, fg="green")


@roles.command("add")
@click.argument("user")
@click.argument("role")
@with_appcontext
@commit
def roles_add(user, role):
    """Add user to role."""
    user, role = _datastore._prepare_role_modify_args(user, role)
    if user is None:
        raise click.UsageError("Cannot find user.")
    if role is None:
        raise click.UsageError("Cannot find role.")
    if _datastore.add_role_to_user(user, role):
        click.secho(
            'Role "{0}" added to user "{1}" ' "successfully.".format(role, user),
            fg="green",
        )
    else:
        raise click.UsageError("Cannot add role to user.")


@roles.command("remove")
@click.argument("user")
@click.argument("role")
@with_appcontext
@commit
def roles_remove(user, role):
    """Remove user from role."""
    user, role = _datastore._prepare_role_modify_args(user, role)
    if user is None:
        raise click.UsageError("Cannot find user.")
    if role is None:
        raise click.UsageError("Cannot find role.")
    if _datastore.remove_role_from_user(user, role):
        click.secho(
            'Role "{0}" removed from user "{1}" ' "successfully.".format(role, user),
            fg="green",
        )
    else:
        raise click.UsageError("Cannot remove role from user.")


@users.command("activate")
@click.argument("user")
@with_appcontext
@commit
def users_activate(user):
    """Activate a user."""
    user_obj = _datastore.get_user(user)
    if user_obj is None:
        raise click.UsageError("ERROR: User not found.")
    if _datastore.activate_user(user_obj):
        click.secho('User "%s" has been activated.' % user, fg="green")
    else:
        click.secho('User "%s" was already activated.' % user, fg="yellow")


@users.command("deactivate")
@click.argument("user")
@with_appcontext
@commit
def users_deactivate(user):
    """Deactivate a user."""
    user_obj = _datastore.get_user(user)
    if user_obj is None:
        raise click.UsageError("ERROR: User not found.")
    if _datastore.deactivate_user(user_obj):
        click.secho('User "%s" has been deactivated.' % user, fg="green")
    else:
        click.secho('User "%s" was already deactivated.' % user, fg="yellow")


@domains.command("create")
@click.argument("domain")
@with_appcontext
def domains_create(domain):
    """Create domain."""
    domain = domain.lower()

    if DomainCategory.get(domain):
        click.secho(f"Domain {domain} already exists.", fg="red")
        return

    try:
        domain_category = DomainCategory.create(domain)
        db.session.merge(domain_category)
        db.session.commit()
    except Exception as error:
        click.secho(f"Domain {domain} creating failed with {error}", fg="red")
    else:
        click.secho(f"Domain {domain} created successfully", fg="green")
