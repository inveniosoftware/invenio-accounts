# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016, 2017 CERN.
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

"""Default configuration for ACCOUNTS."""

ACCOUNTS = True
"""Tells if the templates should use the accounts module.

If False, you won't be able to login via the web UI.
"""

ACCOUNTS_SESSION_REDIS_URL = 'redis://localhost:6379/0'
"""Redis URL used by the module as a cache system for sessions.

It should be in the form ``redis://username:password@host:port/db_index``.
"""

ACCOUNTS_REGISTER_BLUEPRINT = None
"""Register the Security blueprint or not.

It can be used to override the ``register_blueprint`` option.

.. note:: If the value is ``None``, then the blueprint is not registered.
"""

ACCOUNTS_USE_CELERY = None
"""Tells if the module should use Celery or not.

By default, it uses Celery if it can find it.
"""

# Change Flask-Security defaults
SECURITY_CHANGEABLE = True
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

SECURITY_CONFIRMABLE = True
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

SECURITY_PASSWORD_SCHEMES = ['pbkdf2_sha512', 'invenio_aes_encrypted_email']
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

SECURITY_DEPRECATED_PASSWORD_SCHEMES = ['invenio_aes_encrypted_email']
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

SECURITY_RECOVERABLE = True
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

SECURITY_REGISTERABLE = True
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

SECURITY_TRACKABLE = True
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

SECURITY_LOGIN_WITHOUT_CONFIRMATION = True
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

SECURITY_PASSWORD_SALT = None
"""Salt for storing passwords.

Default is `app.config['SECRET_KEY']`.

.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

# Change default templates
SECURITY_FORGOT_PASSWORD_TEMPLATE = 'invenio_accounts/forgot_password.html'
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

SECURITY_LOGIN_USER_TEMPLATE = 'invenio_accounts/login_user.html'
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

SECURITY_REGISTER_USER_TEMPLATE = 'invenio_accounts/register_user.html'
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

SECURITY_RESET_PASSWORD_TEMPLATE = 'invenio_accounts/reset_password.html'
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

SECURITY_CHANGE_PASSWORD_TEMPLATE = 'invenio_accounts/change_password.html'
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

SECURITY_SEND_CONFIRMATION_TEMPLATE = \
    'invenio_accounts/send_confirmation.html'
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

SECURITY_SEND_LOGIN_TEMPLATE = 'invenio_accounts/send_login.html'
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

SECURITY_REGISTER_URL = '/signup/'
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

SECURITY_RESET_URL = '/lost-password/'
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

SECURITY_LOGIN_URL = '/login/'
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

SECURITY_LOGOUT_URL = '/logout/'
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

SECURITY_CHANGE_URL = '/accounts/settings/password/'
"""
.. note:: Overwrite `Flask-Security
   <https://pythonhosted.org/Flask-Security/configuration.html>`_
   configuration.
"""

ACCOUNTS_SETTINGS_SECURITY_TEMPLATE = 'invenio_accounts/settings/security.html'
