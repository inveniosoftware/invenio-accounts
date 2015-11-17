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

"""Invenio user management and authentication."""

from __future__ import absolute_import, print_function

import os

import pkg_resources
from flask import current_app
from flask_kvsession import KVSessionExtension
from flask_login import user_logged_in
from flask_security import Security, changeable, recoverable, registerable, \
    utils
from invenio_db import db
from passlib.registry import register_crypt_handler

from invenio_accounts.forms import confirm_register_form_factory, \
    register_form_factory

from . import config
from .cli import roles as roles_cli
from .cli import users as users_cli
from .datastore import SessionAwareSQLAlchemyUserDatastore
from .hash import InvenioAesEncryptedEmail, _to_binary
from .models import Role, User
from .sessions import login_listener


def get_hmac(password):
    """Override Flask-Security's default MAC signing of plain passwords."""
    return _to_binary(password)


def encrypt_password(password):
    """Override Flask-Security's default encryption function."""
    return current_app.extensions['security'].pwd_context.encrypt(password)


class InvenioAccounts(object):
    """Invenio-Accounts extension."""

    def __init__(self, app=None, sessionstore=None):
        """Extension initialization."""
        self.security = Security()
        self.datastore = None
        if app:
            self.init_app(app, sessionstore=sessionstore)

    @staticmethod
    def monkey_patch_flask_security():
        """Monkey-patch Flask-Security."""
        if utils.get_hmac != get_hmac:
            utils.get_hmac = get_hmac
        if utils.encrypt_password != encrypt_password:
            utils.encrypt_password = encrypt_password
            changeable.encrypt_password = encrypt_password
            recoverable.encrypt_password = encrypt_password
            registerable.encrypt_password = encrypt_password

    def init_app(self, app, use_celery=True, sessionstore=None,
                 register_blueprint=True):
        """Flask application initialization.

        :param sessionstore: store for sessions. Passed to
            ``flask-kvsession``. Defaults to redis.
        :param register_blueprint: Register the Security blueprint or not.
        """
        self.init_config(app)

        # Monkey-patch Flask-Security
        InvenioAccounts.monkey_patch_flask_security()

        # Create user datastore
        if not self.datastore:
            self.datastore = SessionAwareSQLAlchemyUserDatastore(
                db, User, Role)

        # Create sessionstore
        if sessionstore is None:
            if app.testing and \
                    os.environ.get('CI', 'false') == 'false':
                from simplekv.memory import DictStore

                sessionstore = DictStore()
            else:
                import redis
                from simplekv.memory.redisstore import RedisStore

                sessionstore = RedisStore(redis.StrictRedis.from_url(
                    app.config['ACCOUNTS_SESSION_REDIS_URL']))

        user_logged_in.connect(login_listener, app)

        # Initialize extension.
        _register_blueprint = app.config.get('ACCOUNTS_REGISTER_BLUEPRINT')
        if _register_blueprint is not None:
            register_blueprint = _register_blueprint

        state = self.security.init_app(app, datastore=self.datastore,
                                       register_blueprint=register_blueprint)
        self.kvsession_extension = KVSessionExtension(sessionstore, app)

        app.extensions['security'].register_form = register_form_factory(
            app.extensions['security'].register_form, app)

        app.extensions['security'].confirm_register_form = \
            confirm_register_form_factory(
                app.extensions['security'].confirm_register_form, app
            )

        if app.config['ACCOUNTS_USE_CELERY']:
            from invenio_accounts.tasks import send_security_email

            @state.send_mail_task
            def delay_security_email(msg):
                send_security_email.delay(msg.__dict__)

        # Register CLI
        app.cli.add_command(roles_cli, 'roles')
        app.cli.add_command(users_cli, 'users')

        app.extensions['invenio-accounts'] = self

    def init_config(self, app):
        """Initialize configuration."""
        try:
            pkg_resources.get_distribution('celery')
            app.config.setdefault(
                "ACCOUNTS_USE_CELERY", not (app.debug or app.testing))
        except pkg_resources.DistributionNotFound:  # pragma: no cover
            app.config.setdefault("ACCOUNTS_USE_CELERY", False)

        app.config.setdefault('ACCOUNTS', True)

        # Register Invenio legacy password hashing
        register_crypt_handler(InvenioAesEncryptedEmail)

        # Change Flask-Security defaults
        app.config.setdefault('SECURITY_CHANGEABLE', True)
        app.config.setdefault('SECURITY_CONFIRMABLE', True)
        app.config.setdefault('SECURITY_PASSWORD_HASH', 'pbkdf2_sha512')
        app.config.setdefault('SECURITY_PASSWORD_SCHEMES',
                              ['pbkdf2_sha512', 'invenio_aes_encrypted_email'])
        app.config.setdefault('SECURITY_DEPRECATED_PASSWORD_SCHEMES',
                              ['invenio_aes_encrypted_email'])
        app.config.setdefault('SECURITY_RECOVERABLE', True)
        app.config.setdefault('SECURITY_REGISTERABLE', True)
        app.config.setdefault('SECURITY_TRACKABLE', True)
        app.config.setdefault('SECURITY_LOGIN_WITHOUT_CONFIRMATION', True)
        app.config.setdefault('SECURITY_PASSWORD_SALT',
                              app.config['SECRET_KEY'])

        # Change default templates
        app.config.setdefault("SECURITY_FORGOT_PASSWORD_TEMPLATE",
                              "invenio_accounts/forgot_password.html")
        app.config.setdefault("SECURITY_LOGIN_USER_TEMPLATE",
                              "invenio_accounts/login_user.html")
        app.config.setdefault("SECURITY_REGISTER_USER_TEMPLATE",
                              "invenio_accounts/register_user.html")
        app.config.setdefault("SECURITY_RESET_PASSWORD_TEMPLATE",
                              "invenio_accounts/reset_password.html")
        app.config.setdefault("SECURITY_CHANGE_PASSWORD_TEMPLATE",
                              "invenio_accounts/change_password.html")
        app.config.setdefault("SECURITY_SEND_CONFIRMATION_TEMPLATE",
                              "invenio_accounts/send_confirmation.html")
        app.config.setdefault("SECURITY_SEND_LOGIN_TEMPLATE",
                              "invenio_accounts/send_login.html")
        app.config.setdefault("SECURITY_REGISTER_URL",
                              "/signup/")
        app.config.setdefault("SECURITY_RESET_URL",
                              "/lost-password/")
        app.config.setdefault("SECURITY_LOGIN_URL",
                              "/login/")
        app.config.setdefault("SECURITY_LOGOUT_URL",
                              "/logout/")
        app.config.setdefault("SECURITY_CHANGE_URL",
                              "/accounts/settings/password/")

        for k in dir(config):
            if k.startswith('ACCOUNTS_'):
                app.config.setdefault(k, getattr(config, k))


class InvenioAccountsREST(InvenioAccounts):
    """Invenio-Accounts REST extension."""

    def init_app(self, app, use_celery=True, sessionstore=None,
                 register_blueprint=False):
        """Flask application initialization.

        :param sessionstore: store for sessions. Passed to
            ``flask-kvsession``. Defaults to redis.
        :param register_blueprint: Do not register the Security blueprint
            by default.
        """
        return super(InvenioAccountsREST, self).init_app(
            app, use_celery=use_celery, sessionstore=sessionstore,
            register_blueprint=register_blueprint,
        )
