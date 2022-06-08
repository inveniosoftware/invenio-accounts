# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Session-aware datastore."""

from flask_security import SQLAlchemyUserDatastore

from .proxies import current_db_change_history
from .sessions import delete_user_sessions
from .signals import datastore_post_commit, datastore_pre_commit


class SessionAwareSQLAlchemyUserDatastore(SQLAlchemyUserDatastore):
    """Datastore which deletes active session when a user is deactivated."""

    def deactivate_user(self, user):
        """Deactivate a  user.

        :param user: A :class:`invenio_accounts.models.User` instance.
        :returns: The datastore instance.
        """
        res = super(SessionAwareSQLAlchemyUserDatastore, self).deactivate_user(user)
        if res:
            delete_user_sessions(user)
        return res

    def commit(self):
        """Commit a user to its session."""
        datastore_pre_commit.send(session=self.db.session)
        super().commit()
        datastore_post_commit.send(session=self.db.session)

    def mark_changed(self, sid, uid=None, rid=None):
        """Save a user to the changed history."""
        if uid:
            current_db_change_history.updated_users[sid].append(uid)
        elif rid:
            current_db_change_history.updated_roles[sid].append(uid)
