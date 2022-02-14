# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Database models for accounts."""

from datetime import datetime

from flask import current_app, session
from flask_security import RoleMixin, UserMixin
from invenio_db import db
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import validates
from sqlalchemy_utils import IPAddressType, Timestamp

from .errors import AlreadyLinkedError

userrole = db.Table(
    'accounts_userrole',
    db.Column('user_id', db.Integer(), db.ForeignKey(
        'accounts_user.id', name='fk_accounts_userrole_user_id')),
    db.Column('role_id', db.Integer(), db.ForeignKey(
        'accounts_role.id', name='fk_accounts_userrole_role_id')),
)
"""Relationship between users and roles."""


class Role(db.Model, Timestamp, RoleMixin):
    """Role data model."""

    __tablename__ = "accounts_role"

    id = db.Column(db.Integer(), primary_key=True)

    name = db.Column(db.String(80), unique=True)
    """Role name."""

    description = db.Column(db.String(255))
    """Role description."""

    # Enables SQLAlchemy version counter
    version_id = db.Column(db.Integer, nullable=False)
    """Used by SQLAlchemy for optimistic concurrency control."""

    __mapper_args__ = {
        "version_id_col": version_id
    }

    def __str__(self):
        """Return the name and description of the role."""
        return '{0.name} - {0.description}'.format(self)


class User(db.Model, Timestamp, UserMixin):
    """User data model."""

    __tablename__ = "accounts_user"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(255), unique=True)
    """User email."""

    password = db.Column(db.String(255))
    """User password."""

    active = db.Column(db.Boolean(name='active'))
    """Flag to say if the user is active or not ."""

    confirmed_at = db.Column(db.DateTime)
    """When the user confirmed the email address."""

    roles = db.relationship('Role', secondary=userrole,
                            backref=db.backref('users', lazy='dynamic'))
    """List of the user's roles."""

    # Enables SQLAlchemy version counter
    version_id = db.Column(db.Integer, nullable=False)
    """Used by SQLAlchemy for optimistic concurrency control."""

    __mapper_args__ = {
        "version_id_col": version_id
    }

    login_info = db.relationship(
        "LoginInformation", back_populates="user", uselist=False, lazy="joined"
    )

    def _get_login_info_attr(self, attr_name):
        if self.login_info is None:
            return None
        return getattr(self.login_info, attr_name)

    def _set_login_info_attr(self, attr_name, value):
        if self.login_info is None:
            self.login_info = LoginInformation()
        setattr(self.login_info, attr_name, value)

    @property
    def current_login_at(self):
        """When user logged into the current session."""
        return self._get_login_info_attr("current_login_at")

    @property
    def current_login_ip(self):
        """Current user IP address."""
        return self._get_login_info_attr("current_login_ip")

    @property
    def last_login_at(self):
        """When the user logged-in for the last time."""
        return self._get_login_info_attr("last_login_at")

    @property
    def last_login_ip(self):
        """Last user IP address."""
        return self._get_login_info_attr("last_login_ip")

    @property
    def login_count(self):
        """Count how many times the user logged in."""
        return self._get_login_info_attr("login_count")

    @current_login_at.setter
    def current_login_at(self, value):
        return self._set_login_info_attr("current_login_at", value)

    @current_login_ip.setter
    def current_login_ip(self, value):
        return self._set_login_info_attr("current_login_ip", value)

    @last_login_at.setter
    def last_login_at(self, value):
        return self._set_login_info_attr("last_login_at", value)

    @last_login_ip.setter
    def last_login_ip(self, value):
        return self._set_login_info_attr("last_login_ip", value)

    @login_count.setter
    def login_count(self, value):
        return self._set_login_info_attr("login_count", value)

    def __str__(self):
        """Representation."""
        return 'User <id={0.id}, email={0.email}>'.format(self)


class LoginInformation(db.Model):
    """Login information for a user."""

    __tablename__ = "accounts_user_login_information"

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(User.id, name='fk_accounts_login_information_user_id'),
        primary_key=True,
    )
    """ID of user to whom this information belongs."""

    user = db.relationship("User", back_populates="login_info")
    """User to whom this information belongs."""

    last_login_at = db.Column(db.DateTime)
    """When the user logged-in for the last time."""

    current_login_at = db.Column(db.DateTime)
    """When user logged into the current session."""

    last_login_ip = db.Column(IPAddressType, nullable=True)
    """Last user IP address."""

    current_login_ip = db.Column(IPAddressType, nullable=True)
    """Current user IP address."""

    login_count = db.Column(db.Integer)
    """Count how many times the user logged in."""

    @validates('last_login_ip', 'current_login_ip')
    def validate_ip(self, key, value):
        """Hack untrackable IP addresses."""
        # NOTE Flask-Security stores 'untrackable' value to IPAddressType
        #      field. This incorrect value causes ValueError on loading
        #      user object.
        if value == 'untrackable':  # pragma: no cover
            value = None
        return value


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

    user_id = db.Column(db.Integer, db.ForeignKey(
        User.id, name='fk_accounts_session_activity_user_id'))
    """ID of user to whom this session belongs."""

    user = db.relationship(User, backref='active_sessions')

    ip = db.Column(db.String(80), nullable=True)
    """IP address."""

    country = db.Column(db.String(3), nullable=True)
    """Country name."""

    browser = db.Column(db.String(80), nullable=True)
    """User browser."""

    browser_version = db.Column(db.String(30), nullable=True)
    """Browser version."""

    os = db.Column(db.String(80), nullable=True)
    """User operative system name."""

    device = db.Column(db.String(80), nullable=True)
    """User device."""

    @classmethod
    def query_by_expired(cls):
        """Query to select all expired sessions."""
        lifetime = current_app.permanent_session_lifetime
        expired_moment = datetime.utcnow() - lifetime
        return cls.query.filter(cls.created < expired_moment)

    @classmethod
    def query_by_user(cls, user_id):
        """Query to select user sessions."""
        return cls.query.filter_by(user_id=user_id)

    @classmethod
    def is_current(cls, sid_s):
        """Check if the session is the current one."""
        return session.sid_s == sid_s


class UserIdentity(db.Model, Timestamp):
    """Represent a UserIdentity record."""

    __tablename__ = 'accounts_useridentity'

    id = db.Column(db.String(255), primary_key=True, nullable=False)
    method = db.Column(db.String(255), primary_key=True, nullable=False)
    id_user = db.Column(db.Integer(),
                        db.ForeignKey(User.id), nullable=False)

    user = db.relationship(User, backref='external_identifiers')

    __table_args__ = (
        db.Index(
            'accounts_useridentity_id_user_method',
            id_user,
            method,
            unique=True
        ),
    )

    @classmethod
    def get_user(cls, method, external_id):
        """Get the user for a given identity."""
        identity = cls.query.filter_by(
            id=external_id, method=method).one_or_none()
        if identity is not None:
            return identity.user
        return None

    @classmethod
    def create(cls, user, method, external_id):
        """Link a user to an external id.

        :param user: A :class:`invenio_accounts.models.User` instance.
        :param method: The identity source (e.g. orcid, github)
        :param method: The external identifier.
        :raises AlreadyLinkedError: Raised if already exists a link.
        """
        try:
            with db.session.begin_nested():
                db.session.add(cls(
                    id=external_id,
                    method=method,
                    id_user=user.id
                ))
        except IntegrityError:
            raise AlreadyLinkedError(
                # dict used for backward compatibility (came from oauthclient)
                user, {"id": external_id, "method": method})

    @classmethod
    def delete_by_external_id(cls, method, external_id):
        """Unlink a user from an external id."""
        with db.session.begin_nested():
            cls.query.filter_by(id=external_id, method=method).delete()

    @classmethod
    def delete_by_user(cls, method, user):
        """Unlink a user from an external id."""
        with db.session.begin_nested():
            cls.query.filter_by(id_user=user.id, method=method).delete()
