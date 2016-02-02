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

"""Database models for accounts."""

from __future__ import absolute_import, print_function

from flask_security import RoleMixin, UserMixin
from invenio_db import db
from sqlalchemy.orm import validates
from sqlalchemy_utils import IPAddressType, Timestamp

userrole = db.Table(
    'accounts_userrole',
    db.Column('user_id', db.Integer(), db.ForeignKey('accounts_user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('accounts_role.id')),
)


class Role(db.Model, RoleMixin):
    """Role data model."""

    __tablename__ = "accounts_role"

    id = db.Column(db.Integer(), primary_key=True)

    name = db.Column(db.String(80), unique=True)

    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    """User data model."""

    __tablename__ = "accounts_user"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(255), unique=True)

    password = db.Column(db.String(255))

    active = db.Column(db.Boolean)

    confirmed_at = db.Column(db.DateTime)

    last_login_at = db.Column(db.DateTime)

    current_login_at = db.Column(db.DateTime)

    last_login_ip = db.Column(IPAddressType, nullable=True)

    current_login_ip = db.Column(IPAddressType, nullable=True)

    login_count = db.Column(db.Integer)

    roles = db.relationship('Role', secondary=userrole,
                            backref=db.backref('users', lazy='dynamic'))

    @validates('last_login_ip', 'current_login_ip')
    def validate_ip(self, key, value):
        """Hack untrackable IP addresses."""
        # NOTE Flask-Security stores 'untrackable' value to IPAddressType
        #      field. This incorrect value causes ValueError on loading
        #      user object.
        if value == 'untrackable':  # pragma: no cover
            value = None
        return value

    def __str__(self):
        """Representation."""
        return 'User <id={0.id}, email={0.email}>'.format(self)


class SessionActivity(db.Model, Timestamp):
    """User Session Activity model.

    Instances of this model correspond to a session belonging to a user.
    """

    __tablename__ = "accounts_user_session_activity"

    sid_s = db.Column(db.String(255), primary_key=True)
    """Serialized Session ID. Used as the session's key in the kv-session
    store employed by `flask-kvsession`.
    Named here as it is in `flask-kvsession` to avoid confusion.
    """

    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    """ID of user to whom this session belongs."""

    user = db.relationship(User, backref='active_sessions')
