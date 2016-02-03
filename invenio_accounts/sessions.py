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

"""Backend session management for accounts.

The actual backend sessions are provided by ``flask-kvsession``.
This module provides management functionality and populates the
:class:`invenio_accounts.models.SessionActivity` table as new sessions are
created.
"""

from __future__ import absolute_import, print_function

import flask
from flask_login import user_logged_in
from invenio_db import db as _db
from sqlalchemy.exc import IntegrityError
from werkzeug.local import LocalProxy

from invenio_accounts.models import SessionActivity

_sessionstore = LocalProxy(lambda: flask.current_app.
                           extensions['invenio-accounts'].sessionstore)


def add_session(session=None):
    r"""Add a session to the SessionActivity table.

    :param session: Flask Session object to add. If None, ``flask.session``
        is used. The object is expected to have a dictionary entry named
        ``"user_id"`` and a field ``sid_s``
    """
    user_id, sid_s = session['user_id'], session.sid_s
    session_activity = SessionActivity(user_id=user_id, sid_s=sid_s)
    with _db.session.begin_nested():
            _db.session.add(session_activity)
    _db.session.commit()


def login_listener(app, user):
    """Connect to the user_logged_in signal for table population."""
    @flask.after_this_request
    def populate_session_activity(response):
        """Add the current session to the SessionActivity table."""
        # Have to save the session so that the sid_s gets generated.
        app.session_interface.save_session(app, flask.session, response)
        add_session(flask.session)
        return response


def delete_session(sid_s):
    """Delete entries in the data- and kvsessionstore with the given sid_s.

    On a successful deletion, the flask-kvsession store returns 1 while the
    sqlalchemy datastore returns None.

    :returns: 1 if deletion was successful.
    """
    # Remove entries from sessionstore
    _sessionstore.delete(sid_s)
    # Find and remove the corresponding SessionActivity entry
    with _db.session.begin_nested():
        sessionactivity = _db.session.query(SessionActivity).\
            filter_by(sid_s=sid_s).first()
        _db.session.delete(sessionactivity)
    _db.session.commit()
    return 1
