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

from __future__ import absolute_import, print_function

import flask_login

from flask_security import url_for_security
from flask_security.utils import encrypt_password

from invenio_accounts import InvenioAccounts, testutils
from invenio_accounts.views import blueprint

import pytest


def test_client_authenticated(app):
    """Tests for testutils.py:client_authenticated(client).

    We want to verify that it doesn't return True when the client isn't
    authenticated/logged in."""
    ext = InvenioAccounts(app)
    # Required for the test app/templates
    app.register_blueprint(blueprint)

    email = 'test@test.org'
    password = '1234'

    with app.app_context():
        with app.test_client() as client:
            # At this point we should not be authenticated/logged in as a user
            assert not flask_login.current_user
            assert not testutils.client_authenticated(client)

            # What's the status like when we're not logged in?
            # get but don't follow redirects
            # url_for_security(page) returns the internal resource location
            # for the page (e.g. '/login' for 'login'), not the full URL
            change_password_url = url_for_security('change_password')
            response = client.get(change_password_url)
            assert response.status_code == 302
            assert change_password_url not in response.location
            assert url_for_security('login') in response.location

            # Once more, following redirects
            response = client.get(change_password_url, follow_redirects=True)
            assert response.status_code == 200
            assert response.location is None

            # Create a user manually directly in the datastore
            ext.datastore.create_user(email=email,
                                      password=encrypt_password(password))

            # Manual login via view
            response = client.post(url_for_security('login'),
                                   data={'email': email,
                                         'password': password},
                                   environ_base={'REMOTE_ADDR': '127.0.0.1'})
            # client gets redirected after logging in
            assert response.status_code == 302
            assert testutils.client_authenticated(client)
            assert flask_login.current_user.is_authenticated()
            # `is_authenticated()` returns True as long as the user object
            # isn't anonymous, i.e. it's an actual user.

            response = client.get(change_password_url)
            assert response.status_code == 200
            response = client.get(change_password_url, follow_redirects=True)
            assert response.status_code == 200


def test_create_test_user(app):
    """Tests for testutils.py:create_test_user().

    Demonstrates basic usage and context requirements."""
    ext = InvenioAccounts(app)
    email = 'test@test.org'
    password = '1234'

    # Can't access the datastore outside of an application context
    with pytest.raises(RuntimeError):
        testutils.create_test_user(email, password)

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
            user_copy = testutils.create_test_user(email, password)
        # No more tests here b/c the sqlalchemy session crashes when we try to
        # create a user with a duplicate email.


def test_login_user_via_view(app):
    """Tests the login-via-view function/hack."""
    ext = InvenioAccounts(app)
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
