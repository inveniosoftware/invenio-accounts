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

"""Invenio user management and authentication."""

from __future__ import absolute_import, print_function

import pkg_resources
from flask.ext.security import Security, SQLAlchemyUserDatastore
from invenio_db import db

from .cli import roles as roles_cli
from .cli import users as users_cli
from .models import Role, User


class InvenioAccounts(object):
    """Invenio-Accounts extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        self.security = Security()
        self.datastore = None
        if app:
            self.init_app(app)

    def init_app(self, app, use_celery=True):
        """Flask application initialization."""
        self.init_config(app)

        # Create user datastore
        self.datastore = SQLAlchemyUserDatastore(db, User, Role)

        # Initialize extension.
        state = self.security.init_app(app, datastore=self.datastore)

        if app.config['ACCOUNTS_USE_CELERY']:
            from invenio_accounts.tasks import send_security_email

            @state.send_mail_task
            def delay_security_email(msg):
                send_security_email.delay(msg)

        # Register CLI
        app.cli.add_command(roles_cli, 'roles')
        app.cli.add_command(users_cli, 'users')

        app.extensions['invenio-accounts'] = self

    def init_config(self, app):
        """Initialize configuration."""
        try:
            pkg_resources.get_distribution('celery')
            app.config.setdefault("ACCOUNTS_USE_CELERY", True)
        except pkg_resources.DistributionNotFound:
            app.config.setdefault("ACCOUNTS_USE_CELERY", False)

        app.config.setdefault('ACCOUNTS', True)

        # Change Flask-Security defaults
        app.config.setdefault('SECURITY_CHANGEABLE', True)
        app.config.setdefault('SECURITY_CONFIRMABLE', True)
        app.config.setdefault('SECURITY_PASSWORD_HASH', 'pbkdf2_sha512')
        app.config.setdefault('SECURITY_PASSWORD_SCHEMES', ['pbkdf2_sha512'])
        app.config.setdefault('SECURITY_DEPRECATED_PASSWORD_SCHEMES', [])
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
                              "/signup")
