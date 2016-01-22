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


"""Test test utilities."""

from __future__ import absolute_import, print_function

import flask_login
import pytest
from flask_security import url_for_security
from flask_security.utils import encrypt_password
from invenio_db import db

from invenio_accounts import InvenioAccounts, testutils
from invenio_accounts.views import blueprint


def test_client_authenticated(app):
    """Test for testutils.py:client_authenticated(client).

    We want to verify that it doesn't return True when the client isn't
    authenticated/logged in."""
    ext = InvenioAccounts(app)
    # Required for the test app/templates
    app.register_blueprint(blueprint)

    email = 'test@test.org'
    password = '123456'

    with app.app_context():
        change_password_url = url_for_security('change_password')
        login_url = url_for_security('login')

    with app.test_client() as client:
        # At this point we should not be authenticated/logged in as a user
        assert flask_login.current_user.is_anonymous
        assert not testutils.client_authenticated(
            client, test_url=change_password_url)

        # Test HTTP status code of view when not logged in.
        response = client.get(change_password_url)
        assert response.status_code == 302
        assert change_password_url not in response.location
        assert login_url in response.location

        # Once more, following redirects.
        response = client.get(change_password_url, follow_redirects=True)
        assert response.status_code == 200
        assert response.location is None

        # Create a user manually directly in the datastore
        ext.datastore.create_user(email=email,
                                  password=encrypt_password(password))
        db.session.commit()

        # Manual login via view
        response = client.post(login_url,
                               data={'email': email, 'password': password},
                               environ_base={'REMOTE_ADDR': '127.0.0.1'})

        # Client gets redirected after logging in
        assert response.status_code == 302
        assert testutils.client_authenticated(client)
        assert flask_login.current_user.is_authenticated
        # `is_authenticated` returns True as long as the user object
        # isn't anonymous, i.e. it's an actual user.

        response = client.get(change_password_url)
        assert response.status_code == 200
        response = client.get(change_password_url, follow_redirects=True)
        assert response.status_code == 200


def test_create_test_user(app):
    """Test for testutils.py:create_test_user().

    Demonstrates basic usage and context requirements."""
    ext = InvenioAccounts(app)
    email = 'test@test.org'
    password = '1234'

    with app.app_context():
        user = testutils.create_test_user(email, password)
        assert user.password_plaintext == password
        # Will fail if the app is configured to not "encrypt" the passwords.
        assert user.password != password

        # Verify that user exists in app's datastore
        user_ds = ext.datastore.find_user(email=email)
        assert user_ds
        assert user_ds.password == user.password

        with pytest.raises(Exception):
            # Catch-all "Exception" because it's raised by the datastore,
            # and the actual exception type will probably vary depending on
            # which datastore we're running the tests with.
            testutils.create_test_user(email, password)
        # No more tests here b/c the sqlalchemy session crashes when we try to
        # create a user with a duplicate email.


def test_create_test_user_defaults(app):
    """Test the default values for testutils.py:create_test_user."""

    ext = InvenioAccounts(app)
    app.register_blueprint(blueprint)
    with app.app_context():
        user = testutils.create_test_user()
        with app.test_client() as client:
            testutils.login_user_via_view(client, user.email,
                                          user.password_plaintext)
            assert testutils.client_authenticated(client)

        # Create a second user with default params
        user_two = testutils.create_test_user()
        assert not user_two.email == user.email
        ext.datastore.db.session.delete(user)
        ext.datastore.commit()
        user_three = testutils.create_test_user()
        assert not user_three.email == user_two.email


def test_login_user_via_view(app):
    """Test the login-via-view function/hack."""
    InvenioAccounts(app)
    app.register_blueprint(blueprint)
    email = 'test@test.org'
    password = '1234'

    with app.app_context():
        user = testutils.create_test_user(email, password)
        with app.test_client() as client:
            assert not testutils.client_authenticated(client)
            testutils.login_user_via_view(client, user.email,
                                          user.password_plaintext)
            assert testutils.client_authenticated(client)
