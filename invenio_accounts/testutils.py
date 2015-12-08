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

"""Invenio-Accounts utility functions for tests and testing purposes.

.. warning:: DO NOT USE IN A PRODUCTION ENVIRONMENT.

Functions within accessing the datastore will throw an error if called outside
of an application context. If pytest-flask is installed you don't have to worry
about this.
"""

from __future__ import absolute_import, print_function

import datetime

import flask
import flask_login
from flask import current_app
from flask_kvsession import SessionID
from flask_security import url_for_security
from flask_security.utils import encrypt_password
from werkzeug.local import LocalProxy

# "Convenient references" (lifted from flask_security source)
_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


def create_test_user(email='test@test.org',
                     password='123456', **kwargs):
    """Create a user in the datastore, bypassing the registration process.

    Accesses the application's datastore. An error is thrown if called from
    outside of an application context.

    Returns the created user model object instance, with the plaintext password
    as `user.password_plaintext`.
    """
    assert flask.current_app.testing
    encrypted_password = encrypt_password(password)
    user = _datastore.create_user(email=email, password=encrypted_password,
                                  **kwargs)
    _datastore.commit()
    user.password_plaintext = password
    return user


def login_user_via_view(client, email=None, password=None, user=None,
                        login_url=None):
    r"""Attempt to log the given user in via the 'login' view on the client.

    :param client: client to send the request from.
    :param email: email of user account to log in with.
    :param password: password of user account to log in with.
    :param user: If present, ``user.email`` and ``user.password_plaintext`` \
        take precedence over the `email` and `password` parameters.
    :type user: :class:`invenio_accounts.models.User` (with the addition of \
        a ``password_plaintext`` field)
    :param login_url: URL to post login details to. Defaults to the current \
        application's login URL.

    :returns: The response object from the POST to the login form.
    """
    if user is not None:
        email = user.email
        password = user.password_plaintext
    return client.post(login_url or url_for_security('login'),
                       data={'email': email, 'password': password},
                       environ_base={'REMOTE_ADDR': '127.0.0.1'})
    # If the REMOTE_ADDR isn't set it'll throw out a ValueError as it attempts
    # to update the User model in the database with 'untrackable' as the new
    # `last_login_ip`.


def client_authenticated(client, test_url=None):
    r"""Attempt to access the change password page with the given client.

    :param test_url: URL to attempt to get. Defaults to the current \
            application's "change password" page.
    :returns: True if the client can get the test_url without getting \
        redirected and ``flask_login.current_user`` is not anonymous \
        after requesting the page.
    """
    response = client.get(test_url or url_for_security('change_password'))

    return (response.status_code == 200 and
            not flask_login.current_user.is_anonymous)


def webdriver_authenticated(webdriver, test_url=None):
    """Attempt to get the change password page through the given webdriver.

    Similar to `client_authenticated`, but for selenium webdriver objects.
    """
    save_url = webdriver.current_url

    webdriver.get(test_url or flask.url_for('security.change_password',
                                            _external=True))
    result_url = webdriver.current_url
    webdriver.get(save_url)
    return (flask.url_for('security.login', _external=True) not in result_url)


def get_cookie_from_client(client, sid_s=None):
    """Extract the cookie from the client's cookie jar.

    If `sid_s` is None, it returns the first cookie.
    """
    for c in client.cookie_jar:
        if sid_s is None or sid_s in c.value:
            return c


def get_sid_s_from_cookie(cookie):
    """Extract the sid_s from the given cookie."""
    return cookie.value.split('.')[0]


def get_kvsession_keys():
    """Return the key (sid_s) entries in the application's kvsession store."""
    return current_app.kvsession_store.keys()


def unserialize_session(sid_s):
    """Return the unserialized session."""
    return SessionID.unserialize(sid_s)


def set_app_session_ttl(app=None, seconds=None, timedelta=None):
    """Set `PERMANENT_SESSION_LIFETIME` for the provided app.

    If `app` is None it is set for `flask.current_app`.
    The value is set to the provided number of `seconds`
    or (if `seconds` is none absent), the  value of the timedelta.

    Returns the new value of the config variable.
    """
    app = app or flask.current_app
    ttl = timedelta or datetime.timedelta(0, seconds)
    app.config['PERMANENT_SESSION_LIFETIME'] = ttl
    return ttl


def let_session_expire(sid_s=None):
    r"""Do nothing until the given sid has expired.

    .. warning:: Don't use this unless the ``PERMANENT_SESSION_LIFETIME`` of \
        the current app is relatively short -- it defaults to **31 days**.

    :param sid_s: serialized session ID of the session to let expire. If \
        None, ``flask.session`` is used.

    """
    sid = unserialize_session(sid_s or flask.session.sid_s)
    ttl = flask.current_app.config['PERMANENT_SESSION_LIFETIME']
    while not sid.has_expired(ttl):
        pass
    return


def create_sessions_for_user(app=None, user=None, n=1):
    r"""Create a bunch of sessions for the user by logging in with test clients.

    :param app: Flask app to use. If None, ``flask.current_app`` is used.
    :param user: User for which sessions are created. If None, a user is \
        created via :func:`create_test_user`.
    :param n: Number of sessions to create.

    :returns: Dict containing the user and a list containing the clients \
        used to log in.
    """
    app = app or flask.current_app
    user = user or create_test_user()
    client_list = []
    for i in range(0, n):
        with app.test_client() as client:
            login_user_via_view(client, user=user)
            client_list.append(client)

    return {'user': user, 'clients': client_list}
