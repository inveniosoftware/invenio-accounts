# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016, 2017 CERN.
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
import six
from flask import current_app, session
from flask_kvsession import KVSessionExtension
from flask_login import LoginManager, user_logged_in, user_logged_out
from flask_security import Security, changeable, recoverable, registerable, \
    utils
from invenio_db import db
from passlib.registry import register_crypt_handler
from werkzeug.utils import cached_property, import_string

from invenio_accounts.forms import confirm_register_form_factory, \
    login_form_factory, register_form_factory

from . import config
from .datastore import SessionAwareSQLAlchemyUserDatastore
from .hash import InvenioAesEncryptedEmail, _to_binary
from .models import Role, User
from .sessions import login_listener, logout_listener


def get_hmac(password):
    """Override Flask-Security's default MAC signing of plain passwords.

    :param password: The plain password.
    :returns: The password hmac.
    """
    return _to_binary(password)


def hash_password(password):
    """Override Flask-Security's default hashing function.

    :param password: The plain password.
    :returns: The hashed password.
    """
    return current_app.extensions['security'].pwd_context.hash(password)


class InvenioAccounts(object):
    """Invenio-Accounts extension."""

    def __init__(self, app=None, sessionstore=None):
        """Extension initialization.

        :param app: The Flask application.
        :param sessionstore: store for sessions. Passed to
            ``flask-kvsession``. Defaults to redis.
        """
        self.security = Security()
        self.datastore = None
        if app:
            self.init_app(app, sessionstore=sessionstore)

    @staticmethod
    def monkey_patch_flask_security():
        """Monkey-patch Flask-Security."""
        if utils.get_hmac != get_hmac:
            utils.get_hmac = get_hmac
        if utils.hash_password != hash_password:
            utils.hash_password = hash_password
            changeable.hash_password = hash_password
            recoverable.hash_password = hash_password
            registerable.hash_password = hash_password

        # Disable remember me cookie generation as it does not work with
        # session activity tracking (a remember me token will bypass revoking
        # of  a session).
        def patch_do_nothing(*args, **kwargs):
            pass
        LoginManager._set_cookie = patch_do_nothing

        # Disable loading user from headers and object because we want to be
        # sure we can load user only through the login form.
        def patch_reload_anonym(self, *args, **kwargs):
            self.reload_user()
        LoginManager._load_from_header = patch_reload_anonym
        LoginManager._load_from_request = patch_reload_anonym

    def load_obj_or_import_string(self, value):
        """Import string or return object.

        :params value: Import path or class object to instantiate.
        :params default: Default object to return if the import fails.
        :returns: The imported object.
        """
        imp = current_app.config.get(value)
        if isinstance(imp, six.string_types):
            return import_string(imp)
        elif imp:
            return imp

    @cached_property
    def jwt_decode_factory(self):
        """Load default JWT veryfication factory."""
        return self.load_obj_or_import_string(
            'ACCOUNTS_JWT_DECODE_FACTORY'
        )

    @cached_property
    def jwt_creation_factory(self):
        """Load default JWT creation factory."""
        return self.load_obj_or_import_string(
            'ACCOUNTS_JWT_CREATION_FACTORY'
        )

    def init_app(self, app, sessionstore=None, register_blueprint=True):
        """Flask application initialization.

        The following actions are executed:

        #. Initialize the configuration.

        #. Monkey-patch Flask-Security.

        #. Create the user datastore.

        #. Create the sessionstore.

        #. Initialize the extension, the forms to register users and
           confirms their emails, the CLI and, if ``ACCOUNTS_USE_CELERY`` is
           ``True``, register a celery task to send emails.

        :param app: The Flask application.
        :param sessionstore: store for sessions. Passed to
            ``flask-kvsession``. If ``None`` then Redis is configured.
            (Default: ``None``)
        :param register_blueprint: If ``True``, the application registers the
            blueprints. (Default: ``True``)
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

        if app.config['ACCOUNTS_SESSION_ACTIVITY_ENABLED']:
            self._enable_session_activity(app=app)

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

        app.extensions['security'].login_form = login_form_factory(
            app.extensions['security'].login_form, app)

        if app.config['ACCOUNTS_USE_CELERY']:
            from invenio_accounts.tasks import send_security_email

            @state.send_mail_task
            def delay_security_email(msg):
                send_security_email.delay(msg.__dict__)

        # Register context processor
        if app.config['ACCOUNTS_JWT_DOM_TOKEN']:
            from invenio_accounts.context_processors.jwt import \
                jwt_proccessor
            app.context_processor(jwt_proccessor)

        app.extensions['invenio-accounts'] = self

    def init_config(self, app):
        """Initialize configuration.

        :param app: The Flask application.
        """
        try:
            pkg_resources.get_distribution('celery')
            app.config.setdefault(
                "ACCOUNTS_USE_CELERY", not (app.debug or app.testing))
        except pkg_resources.DistributionNotFound:  # pragma: no cover
            app.config.setdefault("ACCOUNTS_USE_CELERY", False)

        # Register Invenio legacy password hashing
        register_crypt_handler(InvenioAesEncryptedEmail)

        # Change Flask defaults
        app.config.setdefault(
            'SESSION_COOKIE_SECURE',
            not app.debug
        )

        # Change Flask-Security defaults
        app.config.setdefault(
            'SECURITY_PASSWORD_SALT',
            app.config['SECRET_KEY']
        )

        # Set JWT secret key
        app.config.setdefault(
            'ACCOUNTS_JWT_SECRET_KEY',
            app.config.get(
                'ACCOUNTS_JWT_SECRET_KEY',
                app.config.get('SECRET_KEY')
            )
        )

        config_apps = ['ACCOUNTS', 'SECURITY_']
        for k in dir(config):
            if any([k.startswith(prefix) for prefix in config_apps]):
                app.config.setdefault(k, getattr(config, k))

    def _enable_session_activity(self, app):
        """Enable session activity."""
        user_logged_in.connect(login_listener, app)
        user_logged_out.connect(logout_listener, app)
        from .views.settings import blueprint
        from .views.security import security, revoke_session
        blueprint.route('/security/', methods=['GET'])(security)
        blueprint.route('/sessions/revoke/', methods=['POST'])(revoke_session)


class InvenioAccountsREST(InvenioAccounts):
    """Invenio-Accounts REST extension."""

    def init_app(self, app, sessionstore=None, register_blueprint=False):
        """Flask application initialization.

        :param app: The Flask application.
        :param sessionstore: store for sessions. Passed to
            ``flask-kvsession``. If ``None`` then Redis is configured.
            (Default: ``None``)
        :param register_blueprint: If ``True``, the application registers the
            blueprints. (Default: ``True``)
        """
        return super(InvenioAccountsREST, self).init_app(
            app, sessionstore=sessionstore,
            register_blueprint=register_blueprint,
        )


class InvenioAccountsUI(InvenioAccounts):
    """Invenio-Accounts UI extension."""

    def init_app(self, app, sessionstore=None, register_blueprint=True):
        """Flask application initialization.

        :param app: The Flask application.
        :param sessionstore: store for sessions. Passed to
            ``flask-kvsession``. If ``None`` then Redis is configured.
            (Default: ``None``)
        :param register_blueprint: If ``True``, the application registers the
            blueprints. (Default: ``True``)
        """
        self.make_session_permanent(app)
        return super(InvenioAccountsUI, self).init_app(
            app, sessionstore=sessionstore,
            register_blueprint=register_blueprint
        )

    def make_session_permanent(self, app):
        """Make session permanent by default.

        Set `PERMANENT_SESSION_LIFETIME` to specify time-to-live
        """
        @app.before_request
        def make_session_permanent():
            session.permanent = True
