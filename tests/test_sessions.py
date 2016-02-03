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
import pickle
import time

import flask
import flask_kvsession
import flask_security
import redis
from flask_login import user_logged_in, user_logged_out
from invenio_db import db as _db
from itsdangerous import Signer
from simplekv.memory.redisstore import RedisStore
from werkzeug.local import LocalProxy

from invenio_accounts import InvenioAccounts, testutils
from invenio_accounts.models import SessionActivity
from invenio_accounts.sessions import delete_session, login_listener
from invenio_accounts.views import blueprint

_sessionstore = LocalProxy(lambda: flask.current_app.
                           extensions['invenio-accounts'].sessionstore)


def test_login_listener(app):
    """Test sessions.py:login_listener"""
    InvenioAccounts(app)
    app.register_blueprint(blueprint)

    user = testutils.create_test_user()
    # The SessionActivity table is initially empty
    query = _db.session.query(SessionActivity)
    assert query.count() == 0

    with app.test_client() as client:
        testutils.login_user_via_view(client, user.email,
                                      user.password_plaintext)
        assert testutils.client_authenticated(client)
        # After logging in, a SessionActivity has been created corresponding
        # to the user's session.
        query = _db.session.query(SessionActivity)
        assert query.count() == 1

        session_entry = query.first()
        assert session_entry.user_id == user.id
        assert session_entry.sid_s == flask.session.sid_s


def test_repeated_login_session_population(app):
    """Verify that the number of SessionActivity entries match the number of
    sessions in the kv-store, when logging in with one user."""
    InvenioAccounts(app)
    app.register_blueprint(blueprint)

    user = testutils.create_test_user()
    query = _db.session.query(SessionActivity)
    assert query.count() == len(testutils.get_kvsession_keys())

    with app.test_client() as client:
        # After logging in, there should be one session in the kv-store and
        # one SessionActivity
        testutils.login_user_via_view(client, user=user)
        assert testutils.client_authenticated(client)
        query = _db.session.query(SessionActivity)
        assert query.count() == 1
        assert query.count() == len(testutils.get_kvsession_keys())

        # Sessions are not deleted upon logout
        client.get(flask_security.url_for_security('logout'))
        assert len(testutils.get_kvsession_keys()) == 1
        query = _db.session.query(SessionActivity)
        assert query.count() == len(testutils.get_kvsession_keys())

        # After logging out and back in, the number of sessions correspond to
        # the number of SessionActivity entries.
        testutils.login_user_via_view(client, user=user)
        query = _db.session.query(SessionActivity)
        assert query.count() == len(testutils.get_kvsession_keys())


def test_login_multiple_clients_single_user_session_population(app):
    """Test session population/creation when logging in as the same user from
    multiple clients."""
    InvenioAccounts(app)
    app.register_blueprint(blueprint)

    user = testutils.create_test_user()
    client_count = 3
    clients = [app.test_client() for _ in range(client_count)]
    sid_s_list = []
    for c in clients:
        with c as client:
            testutils.login_user_via_view(client, user=user)
            assert testutils.client_authenticated(client)
            sid_s_list.append(flask.session.sid_s)
            response = client.get(flask_security.url_for_security('logout'))
            assert not testutils.client_authenticated(client)
    # There is now `client_count` existing sessions and SessionActivity
    # entries
    assert len(testutils.get_kvsession_keys()) == client_count
    query = _db.session.query(SessionActivity)
    assert query.count() == client_count
    assert len(user.active_sessions) == client_count


def test_sessionstore_default_ttl_secs(app):
    """Test the `default_ttl_secs` field for simplekv sessionstore backends
    using the TimeToLive-mixin
    (http://pythonhosted.org/simplekv/index.html#simplekv.TimeToLiveMixin)"""
    ttl_seconds = 1
    ttl_delta = datetime.timedelta(0, ttl_seconds)

    sessionstore = RedisStore(redis.StrictRedis())
    sessionstore.default_ttl_secs = ttl_seconds

    ext = InvenioAccounts(app, sessionstore=sessionstore)
    app.register_blueprint(blueprint)

    # Verify that the backend supports ttl
    assert ext.sessionstore.ttl_support

    user = testutils.create_test_user()
    with app.test_client() as client:
        testutils.login_user_via_view(client, user=user)
        sid = testutils.unserialize_session(flask.session.sid_s)
        while not sid.has_expired(ttl_delta):
            pass
        # When we get here the session should have expired.
        # But the client is still authenticated.
        assert testutils.client_authenticated(client)
        # Why? Because `flask_kvsession` doesn't care about the sessionstore's
        # `default_ttl_seconds`. It uses the `PERMANENT_SESSION_LIFETIME`
        # from the app's config.


def test_session_ttl(app):
    """Test actual/working session expiration/TTL settings."""
    ttl_seconds = 1
    # Set ttl to "0 days, 1 seconds"
    ttl_delta = datetime.timedelta(0, ttl_seconds)

    ext = InvenioAccounts(app)
    app.register_blueprint(blueprint)

    assert ext.sessionstore.ttl_support

    # _THIS_ is what flask_kvsession uses to determine default ttl
    # sets default ttl to `ttl_seconds` seconds
    app.config['PERMANENT_SESSION_LIFETIME'] = ttl_delta
    assert app.permanent_session_lifetime.total_seconds() == ttl_seconds

    user = testutils.create_test_user()
    with app.test_client() as client:
        testutils.login_user_via_view(client, user=user)
        assert len(testutils.get_kvsession_keys()) == 1

        sid = testutils.unserialize_session(flask.session.sid_s)
        testutils.let_session_expire()

        assert sid.has_expired(ttl_delta)
        assert not testutils.client_authenticated(client)

        # Expired sessions are automagically removed from the sessionstore
        # Although not _instantly_.
        while len(testutils.get_kvsession_keys()) > 0:
            pass
        assert len(testutils.get_kvsession_keys()) == 0


def test_repeated_login_session_expiration(app):
    """Test that a new session (with a different sid_s) is created when logging
    in again after a previous session has expired."""
    InvenioAccounts(app)
    app.register_blueprint(blueprint)
    ttl_seconds = 1
    ttl_delta = datetime.timedelta(0, ttl_seconds)
    app.config['PERMANENT_SESSION_LIFETIME'] = ttl_delta

    user = testutils.create_test_user()
    with app.test_client() as client:
        testutils.login_user_via_view(client, user=user)
        first_sid_s = flask.session.sid_s
        testutils.let_session_expire()
        assert not testutils.client_authenticated(client)

        app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(0, 10000)
        testutils.login_user_via_view(client, user=user)
        second_sid_s = flask.session.sid_s

        assert not first_sid_s == second_sid_s


def test_session_deletion(app):
    """Test that a user/client is no longer authenticated when its session is
    deleted via `delete_session`."""
    InvenioAccounts(app)
    app.register_blueprint(blueprint)
    user = testutils.create_test_user()

    with app.test_client() as client:
        testutils.login_user_via_view(client, user=user)
        assert testutils.client_authenticated(client)
        assert len(user.active_sessions) == 1
        saved_sid_s = flask.session.sid_s

        delete_session(saved_sid_s)
        # The user now has no active sessions
        assert len(testutils.get_kvsession_keys()) == 0
        assert len(user.active_sessions) == 0
        query = _db.session.query(SessionActivity)
        assert query.count() == 0

        # After deleting the session, the client is not authenticated
        assert not testutils.client_authenticated(client)

        # A new session is created in the kv-sessionstore, but its
        # sid_s is different and the user is not authenticated with it.
        assert len(testutils.get_kvsession_keys()) == 1
        assert not flask.session.sid_s == saved_sid_s
        assert not testutils.client_authenticated(client)
