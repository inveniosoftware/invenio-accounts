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

import pytest
from flask import current_app, url_for
from flask.ext.security.utils import encrypt_password
from flask_admin import menu
from invenio_admin import InvenioAdmin
from invenio_db import db
from werkzeug.local import LocalProxy

from invenio_accounts import InvenioAccounts
from invenio_accounts.cli import users_create

_datastore = LocalProxy(
    lambda: current_app.extensions['security'].datastore
)


def test_admin(app, admin_view):
    """Test flask-admin interace."""

    # Test activation and deactivation

    with app.app_context():
        # create user and save url for testing
        request_url = url_for("user.action_view")
        kwargs = dict(email="test@test.cern", active=False,
                      password=encrypt_password('aafaf4as5fa'))
        _datastore.create_user(**kwargs)
        _datastore.commit()
        inserted_id = _datastore.get_user('test@test.cern').id

    with app.test_client() as client:

        res = client.post(
            request_url,
            data={'rowid': inserted_id, 'action': 'activate'},
            follow_redirects=True
        )
        assert res.status_code == 200

        res = client.post(
            request_url,
            data={'rowid': inserted_id, 'action': 'inactivate'},
            follow_redirects=True
        )
        assert res.status_code == 200

        pytest.raises(
            ValueError, client.post, request_url,
            data={'rowid': -42, 'action': 'inactivate'},
            follow_redirects=True
        )
        pytest.raises(
            ValueError, client.post, request_url,
            data={'rowid': -42, 'action': 'activate'},
            follow_redirects=True
        )


def test_admin_createuser(app, admin_view):
    """Test flask-admin user creation"""

    with app.test_client() as client:
        # Test empty mail form

        res = client.post(
            url_for('user.create_view'),
            data={'email': ''},
            follow_redirects=True
        )
        assert b'This field is required.' in res.data

        # Reproduces the workflow described in #154

        res = client.post(
            url_for('user.create_view'),
            data={'email': 'test1@test.cern'},
            follow_redirects=True
        )
        assert _datastore.get_user('test1@test.cern') is not None

        res = client.post(
            url_for('user.create_view'),
            data={'email': 'test2@test.cern', 'active': 'true'},
            follow_redirects=True
        )
        user = _datastore.get_user('test2@test.cern')
        assert user is not None
        assert user.active is True

        res = client.post(
            url_for('user.create_view'),
            data={'email': 'test3@test.cern', 'active': 'false'},
            follow_redirects=True
        )
        user = _datastore.get_user('test3@test.cern')
        assert user is not None
        assert user.active is False

    user_data = dict(email='test4@test.cern', active=False,
                     password=encrypt_password('123456'))
    _datastore.create_user(**user_data)

    user_data = dict(email='test5@test.cern', active=True,
                     password=encrypt_password('123456'))
    _datastore.create_user(**user_data)

    user_data = dict(email='test6@test.cern', active=False,
                     password=encrypt_password('123456'))
    _datastore.create_user(**user_data)
    _datastore.commit()
    assert _datastore.get_user('test4@test.cern') is not None
    user = _datastore.get_user('test5@test.cern')
    assert user is not None
    assert user.active is True
    user = _datastore.get_user('test6@test.cern')
    assert user is not None
    assert user.active is False
