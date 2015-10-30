# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.


"""Module tests."""

from __future__ import absolute_import, print_function

from flask import Flask
from flask_babelex import Babel
from flask_cli import FlaskCLI
from flask_mail import Mail
from flask_menu import Menu
from invenio_db import InvenioDB

from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User, Role


def test_version():
    """Test version import."""
    from invenio_accounts import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    FlaskCLI(app)
    Babel(app)
    Mail(app)
    InvenioDB(app)
    ext = InvenioAccounts(app)
    assert 'invenio-accounts' in app.extensions

    app = Flask('testapp')
    FlaskCLI(app)
    Babel(app)
    Mail(app)
    InvenioDB(app)
    ext = InvenioAccounts()
    assert 'invenio-accounts' not in app.extensions
    ext.init_app(app)
    assert 'invenio-accounts' in app.extensions


def test_datastore_usercreate(app):
    """Test create user."""
    ext = InvenioAccounts(app)
    ds = ext.datastore

    with app.app_context():
        u1 = ds.create_user(email='info@invenio-software.org', password='1234',
                            active=True)
        ds.commit()
        u2 = ds.find_user(email='info@invenio-software.org')
        assert u1 == u2
        assert 1 == \
            User.query.filter_by(email='info@invenio-software.org').count()


def test_datastore_rolecreate(app):
    """Test create user."""
    ext = InvenioAccounts(app)
    ds = ext.datastore

    with app.app_context():
        r1 = ds.create_role(name='superuser', description='1234')
        ds.commit()
        r2 = ds.find_role('superuser')
        assert r1 == r2
        assert 1 == \
            Role.query.filter_by(name='superuser').count()


def test_datastore_assignrole(app):
    """Create and assign user to role."""
    ext = InvenioAccounts(app)
    ds = ext.datastore

    with app.app_context():
        u = ds.create_user(email='info@invenio-software.org', password='1234',
                           active=True)
        r = ds.create_role(name='superuser', description='1234')
        ds.add_role_to_user(u, r)
        ds.commit()
        u = ds.get_user('info@invenio-software.org')
        assert len(u.roles) == 1
        assert u.roles[0].name == 'superuser'


def test_view(app):
    """Test view."""
    Menu(app)
    InvenioAccounts(app)
    with app.test_client() as client:
        res = client.get("/login")
        assert res.status_code == 200
