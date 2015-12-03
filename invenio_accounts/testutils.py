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

"""Invenio-Accounts utility functions for tests and testing purposes."""

from __future__ import absolute_import, print_function

import flask
import flask_login
from flask import current_app
from flask_security import url_for_security
from flask_security.utils import encrypt_password
from werkzeug.local import LocalProxy

# "Convenient references" (lifted from flask_security source)
_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


def create_test_user(email='test@test.org',
                     password='', **kwargs):
    """Create a user in the datastore, bypassing the registration process.

    Returns the created user model object instance, with the plaintext password
    as `user.password_plaintext`.
    DO NOT USE THIS IN PRODUCTION. IT IS MEANT FOR TESTING PURPOSES ONLY.
    """
    assert flask.current_app.testing
    encrypted_password = encrypt_password(password)
    user = _datastore.create_user(email=email, password=encrypted_password,
                                  **kwargs)
    _datastore.commit()
    user.password_plaintext = password
    return user


def login_user_via_view(client, email, password, login_url=None):
    """Attempt to log the given user in via the 'login' view on the client.

    Returns the response object.
    """
    return client.post(login_url or url_for_security('login'),
                       data={'email': email, 'password': password},
                       environ_base={'REMOTE_ADDR': '127.0.0.1'})
    # If the REMOTE_ADDR isn't set it'll throw out a ValueError as it attempts
    # to update the User model in the database with 'untrackable' as the new
    # `last_login_ip`.


def client_authenticated(client, test_url=None):
    """Attempt to get the change password page with the given client object.

    Returns True if the client can get the change password page without getting
    redirected and flask_login's `current_user` object isn't anonymous.
    """
    response = client.get(test_url or url_for_security('change_password'))

    return (response.status_code == 200 and
            not flask_login.current_user.is_anonymous)
