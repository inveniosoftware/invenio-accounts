# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2023 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Session-aware datastore."""

from flask_security import SQLAlchemyUserDatastore

from .models import Role
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
        current_db_change_history.clear_dirty_sets(self.db.session)

    def put(self, model):
        """Put a user to its session."""
        res = super().put(model)
        self.mark_changed(id(self.db.session), uid=model.id)
        return res

    def mark_changed(self, sid, uid=None, rid=None):
        """Save a user to the changed history."""
        if uid:
            current_db_change_history.add_updated_user(sid, uid)
        elif rid:
            current_db_change_history.add_updated_role(sid, rid)

    def update_role(self, role):
        """Updates roles."""
        role = self.db.session.merge(role)
        self.mark_changed(id(self.db.session), rid=role.id)
        return role

    def create_role(self, **kwargs):
        """Creates and returns a new role from the given parameters."""
        role = super().create_role(**kwargs)
        self.mark_changed(id(self.db.session), rid=role.id)
        return role

    def find_role_by_id(self, role_id):
        """Fetches roles searching by id."""
        return self.role_model.query.filter_by(id=role_id).one_or_none()
