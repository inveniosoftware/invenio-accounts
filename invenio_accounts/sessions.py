# SPDX-FileCopyrightText: 2015-2026 CERN.
# SPDX-FileCopyrightText: 2024 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Backend session management for accounts.

The actual backend sessions are provided by ``flask-kvsession``.
This module provides management functionality and populates the
:class:`invenio_accounts.models.SessionActivity` table as new sessions are
created.
"""

import os
from functools import lru_cache

from flask import after_this_request, current_app, request, session
from invenio_db import db
from invenio_rest.csrf import reset_token
from iptocc import country_code
from ua_parser import user_agent_parser
from werkzeug.local import LocalProxy

from .models import SessionActivity
from .proxies import current_accounts

_sessionstore = LocalProxy(lambda: current_app.kvsession_store)


def _file_signature(path):
    """Return a value that changes when the file at ``path`` is replaced.

    The modification time alone is not enough: it can be kept by the tool that
    copies the file, and it can be too coarse on some file systems. The size
    catches most of those. The inode catches a file that is written next to
    the old one and renamed over it, which is the safe way to refresh a file.
    """
    stat = os.stat(path)
    return stat.st_mtime_ns, stat.st_size, stat.st_ino


@lru_cache(maxsize=2)
def _open_mmdb(path, signature):
    """Open the MaxMind DB at ``path``.

    ``signature`` is only part of the cache key, so that a file that was
    replaced on disk (e.g. by a monthly refresh) is opened again.
    """
    # Imported here so that it is only loaded when the setting is used.
    import maxminddb

    return maxminddb.open_database(path)


def _mmdb_country(path, ip):
    """Look up ``ip`` in the MaxMind DB at ``path``."""
    reader = _open_mmdb(path, _file_signature(path))
    try:
        record = reader.get(ip)
    except ValueError:  # not a valid IP address
        return None
    return (record or {}).get("country", {}).get("iso_code")


def _ip2country(ip):
    """Get user country.

    Uses the MaxMind DB from ``ACCOUNTS_GEOIP_DB_PATH`` if it is set, and
    ``iptocc`` otherwise. If the file cannot be read, logs the error and uses
    ``iptocc``.
    """
    if not ip:
        return None

    path = current_app.config.get("ACCOUNTS_GEOIP_DB_PATH")
    if path:
        try:
            cc = _mmdb_country(path, ip)
        except Exception:
            current_app.logger.exception(
                "Cannot read the GeoIP database from ACCOUNTS_GEOIP_DB_PATH=%r, "
                "falling back to iptocc.",
                path,
            )
            cc = country_code(ip)
    else:
        cc = country_code(ip)

    # "EU" is a registry placeholder, not a country.
    return None if cc == "EU" else cc


def _extract_info_from_useragent(user_agent):
    """Extract extra informations from user."""
    parsed_string = user_agent_parser.Parse(user_agent)
    return {
        "os": parsed_string.get("os", {}).get("family"),
        "browser": parsed_string.get("user_agent", {}).get("family"),
        "browser_version": parsed_string.get("user_agent", {}).get("major"),
        "device": parsed_string.get("device", {}).get("family"),
    }


def add_session(session=None):
    r"""Add a session to the SessionActivity table.

    :param session: Flask Session object to add. If None, ``session``
        is used. The object is expected to have a dictionary entry named
        ``"_user_id"`` and a field ``sid_s``
    """
    if "_user_id" not in session and "user_id" in session:
        # this is to support both flask-login 0.4.x as well as 0.5+,
        # where 'user_id' was renamed to '_user_id'
        session["_user_id"] = session["user_id"]

    user_id, sid_s = session["_user_id"], session.sid_s
    with db.session.begin_nested():
        session_activity = SessionActivity(
            user_id=user_id,
            sid_s=sid_s,
            ip=request.remote_addr,
            country=_ip2country(request.remote_addr),
            **_extract_info_from_useragent(request.headers.get("User-Agent", "")),
        )
        db.session.merge(session_activity)


def login_listener(app, user):
    """Connect to the user_logged_in signal for table population.

    :param app: The Flask application.
    :param user: The :class:`invenio_accounts.models.User` instance.
    """

    @after_this_request
    def add_user_session(response):
        """Regenerate current session and add to the SessionActivity table.

        .. note:: `flask.session.regenerate()` actually calls Flask-KVSession's
            `flask_kvsession.KVSession.regenerate`.
        """
        # Regenerate the session to avoid session fixation vulnerabilities.
        session.regenerate()
        # Save the session first so that the sid_s gets generated.
        app.session_interface.save_session(app, session, response)
        # Don't add impersonation sessions
        if "_impersonator_id" not in session:
            add_session(session)
            current_accounts.datastore.commit()
        return response


def logout_listener(app, user):
    """Connect to the user_logged_out signal.

    :param app: The Flask application.
    :param user: The :class:`invenio_accounts.models.User` instance.
    """

    @after_this_request
    def _commit(response=None):
        if hasattr(session, "sid_s"):
            delete_session(session.sid_s)
        # Regenerate the session to avoid session fixation vulnerabilities.
        session.regenerate()
        current_accounts.datastore.commit()
        return response


def csrf_token_reset(app, user):
    """Connect to the user_logged_in signal to reset the csrf token.

    :param app: The Flask application.
    :param user: The :class:`invenio_accounts.models.User` instance.
    """
    reset_token()


def delete_session(sid_s):
    """Delete entries in the data- and kvsessionstore with the given sid_s.

    On a successful deletion, the flask-kvsession store returns 1 while the
    sqlalchemy datastore returns None.

    :param sid_s: The session ID.
    :returns: ``1`` if deletion was successful.
    """
    # Remove entries from sessionstore
    _sessionstore.delete(sid_s)
    # Check if there is an impersonation session
    if request and "_impersonate_id" in session:
        return 0
    # Find and remove the corresponding SessionActivity entry
    db.session.query(SessionActivity).filter_by(sid_s=sid_s).delete()
    return 1


def delete_user_sessions(user):
    """Delete all active user sessions.

    :param user: User instance.
    :returns: If ``True`` then the session is successfully deleted.
    """
    with db.session.begin_nested():
        for s in user.active_sessions:
            _sessionstore.delete(s.sid_s)

        db.session.query(SessionActivity).filter_by(user=user).delete()

    return True


def default_session_store_factory(app):
    """Session store factory.

    If ``ACCOUNTS_SESSION_REDIS_URL`` is set, it returns a
    :class:`simplekv.memory.redisstore.RedisStore` otherwise
    a :class:`simplekv.memory.DictStore`.
    """
    accounts_session_redis_url = app.config.get("ACCOUNTS_SESSION_REDIS_URL")
    if accounts_session_redis_url:
        import redis
        from simplekv.memory.redisstore import RedisStore

        return RedisStore(redis.StrictRedis.from_url(accounts_session_redis_url))
    from simplekv.memory import DictStore

    return DictStore()
