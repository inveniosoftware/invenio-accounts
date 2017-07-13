..
    This file is part of Invenio.
    Copyright (C) 2017 CERN.

    Invenio is free software; you can redistribute it
    and/or modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the
    Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
    MA 02111-1307, USA.

    In applying this license, CERN does not
    waive the privileges and immunities granted to it by virtue of its status
    as an Intergovernmental Organization or submit itself to any jurisdiction.


Configuration
=============
Invenio-Accounts depends on many existing community packages, so a large part
of the configuration is defined by these packages.

Please refer to the documentation of each package for a full overview over
which configration variables that are available:

- `Flask-Security <https://flask-security.readthedocs.io>`_
- `Flask-Login <https://flask-login.readthedocs.io/>`_
- `Flask-Principal <https://pythonhosted.org/Flask-Principal/>`_
- `Flask-KVSession <http://pythonhosted.org/Flask-KVSession/>`_

Below we only cover the most important configuration options for
Invenio-Accounts.

Secret key
----------
The ``SECRET_KEY`` (see `Flask
<http://flask.pocoo.org/docs/0.12/config/#builtin-configuration-values>`_
documentation) is the most important configuration variable. A large part of
the security of a web application is based on the secrecy of the value. In case
the secret key is leaked, it is imperative that a new secret key is created.

Sessions
--------
Server-side session data is currently stored in Redis, you must therefore
configure where your Redis instance is located using:

.. autodata:: invenio_accounts.config.ACCOUNTS_SESSION_REDIS_URL

If the session activity tracking is enabled you should also ensure that you
regularly clean the session tracking tables for expired sessions. You do this
by configure a Celery schedule similar to this:

.. code-block:: python

    from datetime import timedelta
    CELERYBEAT_SCHEDULE = {
        'session_cleaner': {
            'task': 'invenio_accounts.tasks.clean_session_table',
            'schedule': timedelta(days=1),
        },
    }

Remember me
-----------
Invenio supports a "remember me" feature which allows a user to be logged in,
in case their session expired (which by default happens after 31 days). By
default a user must **opt-in** via a checkbox in the login form. If by default
you instead would like a user to **opt-out**

.. autodata:: invenio_accounts.config.SECURITY_DEFAULT_REMEMBER_ME

Password hashing
----------------
Invenio defaults to use PBKDF2 SHA512 algorithm for password hashing:

.. autodata:: invenio_accounts.config.SECURITY_PASSWORD_HASH

Invenio has support for storing hashes using many different algoritms. For
instance, by default Invenio also supports Invenio v1.x password hashes to make
migration from v1.x easier. Legacy v1.x password hashes will however be
automatically migrated to the new stronger algorithm the next time a user
login. You can control the supported and deprecated algorithms using the
following two configuration variables:

.. autodata:: invenio_accounts.config.SECURITY_PASSWORD_SCHEMES

.. autodata:: invenio_accounts.config.SECURITY_DEPRECATED_PASSWORD_SCHEMES

Recaptcha
---------
The user registration form has support for recaptcha. All you need to do is to
set the following two configuration variables (provided by
`reCAPTCHA <https://www.google.com/recaptcha/>`_ when you register):

.. autodata:: invenio_accounts.config.RECAPTCHA_PUBLIC_KEY

.. autodata:: invenio_accounts.config.RECAPTCHA_PRIVATE_KEY

User tracking
-------------
Invenio-Accounts by default comes with user tracking enabled. The user tracking
can be disabled using the configuration variables:

.. autodata:: invenio_accounts.config.ACCOUNTS_SESSION_ACTIVITY_ENABLED

.. autodata:: invenio_accounts.config.SECURITY_TRACKABLE

When a user login the following information is tracked:

- IP address (current and previous)
- Timestamp (current and previous)
- Login count

A user **do not** have control over above information as it is logged for
security purposes.

In addition Invenio is tracking all active sessions of a user. For each active
session we track:

- IP address
- Country of IP address
- Browser (e.g. Chrome)
- Browser version
- Operating system (e.g. MacOS)
- Device type (e.g. iPhone).

The user **do** have full control over the active sessions, meaning they can
browse and revoke active session resulting in that the information is removed.
The session activity tracking feature is used to allow users to logout from all
their active sessions, but also allow administrators to ban a user and ensure
they are logged out of all active sessions in the application.

Templates
---------
You can customize many of the templates used to render user registration,
login, logout, email confirmations etc. Here are some few of the possiblities:

.. autodata:: invenio_accounts.config.SECURITY_LOGIN_USER_TEMPLATE

.. autodata:: invenio_accounts.config.SECURITY_REGISTER_USER_TEMPLATE

.. autodata:: invenio_accounts.config.SECURITY_RESET_PASSWORD_TEMPLATE

.. autodata:: invenio_accounts.config.SECURITY_FORGOT_PASSWORD_TEMPLATE

.. autodata:: invenio_accounts.config.SECURITY_SEND_CONFIRMATION_TEMPLATE

.. autodata:: invenio_accounts.config.SECURITY_SEND_LOGIN_TEMPLATE

URLs
----
You can also customize the URLs under which you register and login in case you
e.g. do not like the current naming:

.. autodata:: invenio_accounts.config.SECURITY_LOGIN_URL

.. autodata:: invenio_accounts.config.SECURITY_LOGOUT_URL

.. autodata:: invenio_accounts.config.SECURITY_REGISTER_URL

.. autodata:: invenio_accounts.config.SECURITY_RESET_URL

Feature flags
-------------
A lot of the behaviour of Invenio-Accounts can be enabled/disabled depending on
your current needs. Here are some of the feature flag options:

.. autodata:: invenio_accounts.config.SECURITY_REGISTERABLE

.. autodata:: invenio_accounts.config.SECURITY_RECOVERABLE

.. autodata:: invenio_accounts.config.SECURITY_CONFIRMABLE

.. autodata:: invenio_accounts.config.SECURITY_CHANGEABLE

.. autodata:: invenio_accounts.config.SECURITY_LOGIN_WITHOUT_CONFIRMATION
