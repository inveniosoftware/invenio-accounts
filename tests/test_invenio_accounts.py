# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
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

import pytest
from flask import Flask
from flask_babelex import Babel
from flask_mail import Mail
from flask_security import url_for_security
from invenio_db import InvenioDB, db

from invenio_accounts import InvenioAccounts, InvenioAccountsREST
from invenio_accounts.models import Role, User


def test_version():
    """Test version import."""
    from invenio_accounts import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    Babel(app)
    Mail(app)
    InvenioDB(app)
    ext = InvenioAccounts(app)
    assert 'invenio-accounts' in app.extensions
    assert 'security' in app.blueprints.keys()

    app = Flask('testapp')
    Babel(app)
    Mail(app)
    InvenioDB(app)
    ext = InvenioAccounts()
    assert 'invenio-accounts' not in app.extensions
    assert 'security' not in app.blueprints.keys()
    ext.init_app(app)
    assert 'invenio-accounts' in app.extensions
    assert 'security' in app.blueprints.keys()


def test_init_rest():
    """Test REST extension initialization."""
    app = Flask('testapp')
    Babel(app)
    Mail(app)
    InvenioDB(app)
    ext = InvenioAccountsREST(app)
    assert 'invenio-accounts' in app.extensions
    assert 'security' not in app.blueprints.keys()

    app = Flask('testapp')
    Babel(app)
    Mail(app)
    InvenioDB(app)
    ext = InvenioAccountsREST()
    assert 'invenio-accounts' not in app.extensions
    assert 'security' not in app.blueprints.keys()
    ext.init_app(app)
    assert 'invenio-accounts' in app.extensions
    assert 'security' not in app.blueprints.keys()

    app = Flask('testapp')
    app.config['ACCOUNTS_REGISTER_BLUEPRINT'] = True
    Babel(app)
    Mail(app)
    InvenioDB(app)
    ext = InvenioAccountsREST()
    assert 'invenio-accounts' not in app.extensions
    assert 'security' not in app.blueprints.keys()
    ext.init_app(app)
    assert 'invenio-accounts' in app.extensions
    assert 'security' in app.blueprints.keys()


def test_alembic(app):
    """Test alembic recipes."""
    ext = app.extensions['invenio-db']

    if db.engine.name == 'sqlite':
        raise pytest.skip('Upgrades are not supported on SQLite.')

    assert not ext.alembic.compare_metadata()
    db.drop_all()
    ext.alembic.upgrade()

    assert not ext.alembic.compare_metadata()
    ext.alembic.downgrade(target='96e796392533')
    ext.alembic.upgrade()

    assert not ext.alembic.compare_metadata()


def test_datastore_usercreate(app):
    """Test create user."""
    ds = app.extensions['invenio-accounts'].datastore

    with app.app_context():
        u1 = ds.create_user(email='info@inveniosoftware.org', password='1234',
                            active=True)
        ds.commit()
        u2 = ds.find_user(email='info@inveniosoftware.org')
        assert u1 == u2
        assert 1 == \
            User.query.filter_by(email='info@inveniosoftware.org').count()


def test_datastore_rolecreate(app):
    """Test create user."""
    ds = app.extensions['invenio-accounts'].datastore

    with app.app_context():
        r1 = ds.create_role(name='superuser', description='1234')
        ds.commit()
        r2 = ds.find_role('superuser')
        assert r1 == r2
        assert 1 == \
            Role.query.filter_by(name='superuser').count()


def test_datastore_assignrole(app):
    """Create and assign user to role."""
    ds = app.extensions['invenio-accounts'].datastore

    with app.app_context():
        u = ds.create_user(email='info@inveniosoftware.org', password='1234',
                           active=True)
        r = ds.create_role(name='superuser', description='1234')
        ds.add_role_to_user(u, r)
        ds.commit()
        u = ds.get_user('info@inveniosoftware.org')
        assert len(u.roles) == 1
        assert u.roles[0].name == 'superuser'


def test_view(app):
    """Test view."""
    with app.app_context():
        login_url = url_for_security('login')

    with app.test_client() as client:
        res = client.get(login_url)
        assert res.status_code == 200


def test_configuration(base_app):
    """Test configuration."""
    app = base_app
    app.config['ACCOUNTS_USE_CELERY'] = 'deadbeef'
    InvenioAccounts(app)
    assert 'deadbeef' == app.config['ACCOUNTS_USE_CELERY']
