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

"""Session-aware datastore."""

from __future__ import absolute_import, print_function

from flask_security import SQLAlchemyUserDatastore

from .sessions import delete_user_sessions


class SessionAwareSQLAlchemyUserDatastore(SQLAlchemyUserDatastore):
    """Datastore which deletes active session when a user is deactivated."""

    def deactivate_user(self, user):
        """Deactivate a  user.

        :param user: A :class:`invenio_accounts.models.User` instance.
        :returns: The datastore instance.
        """
        res = super(SessionAwareSQLAlchemyUserDatastore, self).deactivate_user(
            user)
        if res:
            delete_user_sessions(user)
        return res
