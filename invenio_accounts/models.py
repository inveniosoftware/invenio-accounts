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

"""Database models for accounts."""

from __future__ import absolute_import, print_function

from flask_security import RoleMixin, UserMixin
from invenio_db import db
from sqlalchemy_utils import IPAddressType

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

    last_login_ip = db.Column(IPAddressType)

    current_login_ip = db.Column(IPAddressType)

    login_count = db.Column(db.Integer)

    roles = db.relationship('Role', secondary=userrole,
                            backref=db.backref('users', lazy='dynamic'))
