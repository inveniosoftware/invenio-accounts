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

"""Test backend sessions."""

import datetime
import time

import flask_security
import pytest
from flask import current_app, session
from invenio_db import db
from simplekv.memory.redisstore import RedisStore
from werkzeug.local import LocalProxy

from invenio_accounts import InvenioAccounts, testutils
from invenio_accounts.models import SessionActivity
from invenio_accounts.sessions import delete_session
from invenio_accounts.views import blueprint

_sessionstore = LocalProxy(lambda: current_app.
                           extensions['invenio-accounts'].sessionstore)
_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


def test_login_listener(app):
    """Test login listener."""
    with app.app_context():
        with app.test_client() as client:
            user = testutils.create_test_user('test@example.org')
            # The SessionActivity table is initially empty
            query = db.session.query(SessionActivity)
            assert query.count() == 0

            testutils.login_user_via_view(client, user.email,
                                          user.password_plaintext)
            assert testutils.client_authenticated(client)
            # After logging in, a SessionActivity has been created
            # corresponding to the user's session.
            query = db.session.query(SessionActivity)
            assert query.count() == 1

            session_entry = query.first()
            assert session_entry.user_id == user.id
            assert session_entry.sid_s == session.sid_s


def test_repeated_login_session_population(app):
    """Verify session population on repeated login."""
    with app.app_context():
        user = testutils.create_test_user('test@example.org')
        query = db.session.query(SessionActivity)
        assert query.count() == len(app.kvsession_store.keys())

        with app.test_client() as client:
            # After logging in, there should be one session in the kv-store and
            # one SessionActivity
            testutils.login_user_via_view(client, user=user)
            assert testutils.client_authenticated(client)
            query = db.session.query(SessionActivity)
            assert query.count() == 1
            assert len(app.kvsession_store.keys()) == 1
            first_login_session_id = app.kvsession_store.keys()[0]

            # Sessions are not deleted upon logout
            client.get(flask_security.url_for_security('logout'))
            assert len(app.kvsession_store.keys()) == 1
            query = db.session.query(SessionActivity)
            assert query.count() == 1
            assert len(app.kvsession_store.keys()) == 1
            # Session id doesn't change after logout
            assert first_login_session_id == app.kvsession_store.keys()[0]

            # After logging out and back in, the inital session id in the
            # sessionstore should be updated, and there should be two
            # SessionActivity entries (the old one and the regenerated).
            testutils.login_user_via_view(client, user=user)
            query = db.session.query(SessionActivity)
            assert query.count() == 2
            assert len(app.kvsession_store.keys()) == 1
            assert first_login_session_id != app.kvsession_store.keys()[0]


def test_login_multiple_clients_single_user_session_population(app):
    """Test session population/creation from multiple clients for same user."""
    with app.app_context():
        user = testutils.create_test_user('test@example.org')

        client_count = 3
        clients = [app.test_client() for _ in range(client_count)]
        sid_s_list = []
        for c in clients:
            with c as client:
                testutils.login_user_via_view(client, user=user)
                assert testutils.client_authenticated(client)
                sid_s_list.append(session.sid_s)
                client.get(flask_security.url_for_security('logout'))
                assert not testutils.client_authenticated(client)
        # There is now `client_count` existing sessions and SessionActivity
        # entries
        assert len(app.kvsession_store.keys()) == client_count
        query = db.session.query(SessionActivity)
        assert query.count() == client_count
        assert len(user.active_sessions) == client_count


def test_sessionstore_default_ttl_secs(app):
    """Test the `default_ttl_secs` field for simplekv sessionstore.

    See http://simplekv.readthedocs.io/index.html#simplekv.TimeToLiveMixin.
    """
    if type(app.kvsession_store) is not RedisStore:
        pytest.skip('TTL support needed, this test requires Redis.')

    ttl_seconds = 3
    ttl_delta = datetime.timedelta(0, ttl_seconds)

    sessionstore = app.kvsession_store
    sessionstore.default_ttl_secs = ttl_seconds

    # Verify that the backend supports ttl
    assert sessionstore.ttl_support

    app.kvsession_store = sessionstore

    with app.app_context():
        user = testutils.create_test_user('test@example.org')

        with app.test_client() as client:
            testutils.login_user_via_view(client, user=user)
            sid = testutils.unserialize_session(session.sid_s)
            while not sid.has_expired(ttl_delta):
                pass
            # When we get here the session should have expired.
            # But the client is still authenticated.
            assert testutils.client_authenticated(client)
            # Why? Because `flask_kvsession` doesn't care about
            # the sessionstore's `default_ttl_seconds`. It uses
            # the `PERMANENT_SESSION_LIFETIME` from the app's config.


def test_session_ttl(app):
    """Test actual/working session expiration/TTL settings."""
    if type(app.kvsession_store) is not RedisStore:
        pytest.skip('TTL support needed, this test requires Redis.')

    ttl_seconds = 3
    # Set ttl to "0 days, 1 seconds"
    ttl_delta = datetime.timedelta(0, ttl_seconds)

    assert app.kvsession_store.ttl_support

    # _THIS_ is what flask_kvsession uses to determine default ttl
    # sets default ttl to `ttl_seconds` seconds
    app.config['PERMANENT_SESSION_LIFETIME'] = ttl_delta
    assert app.permanent_session_lifetime.total_seconds() == ttl_seconds

    with app.app_context():
        user = testutils.create_test_user('test@example.org')

        with app.test_client() as client:
            testutils.login_user_via_view(client, user=user)
            assert len(app.kvsession_store.keys()) == 1

            sid = testutils.unserialize_session(session.sid_s)
            time.sleep(ttl_seconds + 1)

            assert sid.has_expired(ttl_delta)
            assert not testutils.client_authenticated(client)

            # Expired sessions are automagically removed from the sessionstore
            # Although not _instantly_.
            while len(app.kvsession_store.keys()) > 0:
                pass
            assert len(app.kvsession_store.keys()) == 0


def test_repeated_login_session_expiration(app):
    """Test repeated session login.

    Test that a new session (with a different sid_s) is created when logging
    in again after a previous session has expired."""
    ttl_seconds = 3
    ttl_delta = datetime.timedelta(0, ttl_seconds)
    app.config['PERMANENT_SESSION_LIFETIME'] = ttl_delta

    with app.app_context():
        user = testutils.create_test_user('test@example.org')
        with app.test_client() as client:
            testutils.login_user_via_view(client, user=user)
            first_sid_s = session.sid_s
            time.sleep(ttl_seconds + 1)
            assert not testutils.client_authenticated(client)

            app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
                0, 10000)
            testutils.login_user_via_view(client, user=user)
            second_sid_s = session.sid_s

            assert not first_sid_s == second_sid_s


def test_session_deletion(app):
    """Test if user is not authenticated when session is deleted."""
    with app.app_context():
        user = testutils.create_test_user('test@example.org')

        with app.test_client() as client:
            testutils.login_user_via_view(client, user=user)
            assert testutils.client_authenticated(client)
            assert len(user.active_sessions) == 1
            saved_sid_s = session.sid_s

            delete_session(saved_sid_s)
            db.session.commit()
            # The user now has no active sessions
            assert len(app.kvsession_store.keys()) == 0
            assert len(user.active_sessions) == 0
            query = db.session.query(SessionActivity)
            assert query.count() == 0

            # After deleting the session, the client is not authenticated
            assert not testutils.client_authenticated(client)

            # A new session is created in the kv-sessionstore, but its
            # sid_s is different and the user is not authenticated with it.
            assert len(app.kvsession_store.keys()) == 1
            assert not session.sid_s == saved_sid_s
            assert not testutils.client_authenticated(client)


def test_deactivate_user(app):
    """Test deactivation of users."""
    with app.app_context():
        user_bob = testutils.create_test_user(email='bob@bobmail.bob',
                                              password='123',
                                              active=True)
        with app.test_client() as client:
            assert user_bob.active
            assert not testutils.client_authenticated(client)
            testutils.login_user_via_view(client, user_bob.email,
                                          user_bob.password_plaintext)
            assert testutils.client_authenticated(client)
            # Now we deactivate Bob.
            # `deactivate_user` returns True if a change was made.
            _datastore.deactivate_user(user_bob)
            db.session.commit()
            assert not testutils.client_authenticated(client)
