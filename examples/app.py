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


u"""Minimal Flask application example for development.

Install the Invenio default theme

You should execute these commands in the examples-directory.

.. code-block:: console

   $ pip install invenio-theme
   $ pip install invenio-assets
   $ flask -a app.py npm
   $ cd static
   $ npm install
   $ cd ..
   $ flask -a app.py collect -v
   $ flask -a app.py assets build

Create database and tables:

.. code-block:: console

   $ flask -a app.py db init
   $ flask -a app.py db create

Create a user:

.. code-block:: console

   $ flask -a app.py users create info@invenio-software.org -a
   $ flask -a app.py users activate info@invenio-software.org

Run the development server:

.. code-block:: console

   $ flask -a app.py --debug run
   $ flask -a app.py shell
"""

from __future__ import absolute_import, print_function

import os

import pkg_resources
from flask import Flask, render_template
from flask.ext.menu import Menu
from flask_babelex import Babel
from flask_cli import FlaskCLI
from flask_mail import Mail
from flask_security import current_user
from invenio_db import InvenioDB

from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint

try:
    pkg_resources.get_distribution('invenio_assets')
    from invenio_assets import InvenioAssets

    INVENIO_ASSETS_AVAILABLE = True
except pkg_resources.DistributionNotFound:
    INVENIO_ASSETS_AVAILABLE = False

try:
    pkg_resources.get_distribution('invenio_theme')
    from invenio_theme import InvenioTheme

    INVENIO_THEME_AVAILABLE = True
except pkg_resources.DistributionNotFound:
    INVENIO_THEME_AVAILABLE = False

try:
    pkg_resources.get_distribution('invenio_admin')
    from invenio_admin import InvenioAdmin

    INVENIO_ADMIN_AVAILABLE = True
except pkg_resources.DistributionNotFound:
    INVENIO_ADMIN_AVAILABLE = False

# Create Flask application
app = Flask(__name__)
app.config.update(
    ACCOUNTS_USE_CELERY=False,
    CELERY_ALWAYS_EAGER=True,
    CELERY_CACHE_BACKEND="memory",
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    CELERY_RESULT_BACKEND="cache",
    MAIL_SUPPRESS_SEND=True,
    SECRET_KEY="CHANGE_ME",
    SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
)

if os.environ.get('RECAPTCHA_PUBLIC_KEY') is not None \
        and os.environ.get('RECAPTCHA_PRIVATE_KEY') is not None:
    app.config.setdefault('RECAPTCHA_PUBLIC_KEY',
                          os.environ['RECAPTCHA_PUBLIC_KEY'])
    app.config.setdefault('RECAPTCHA_PRIVATE_KEY',
                          os.environ['RECAPTCHA_PRIVATE_KEY'])

FlaskCLI(app)
Babel(app)
Mail(app)
InvenioDB(app)
Menu(app)
InvenioAccounts(app)

if INVENIO_ASSETS_AVAILABLE:
    InvenioAssets(app)
if INVENIO_THEME_AVAILABLE:
    InvenioTheme(app)
if INVENIO_ADMIN_AVAILABLE:
    InvenioAdmin(app, permission_factory=lambda x: x,
                 view_class_factory=lambda x: x)
app.register_blueprint(blueprint)


@app.route("/")
def index():
    """Basic test view."""
    if current_user.is_authenticated:
        return render_template("authenticated.html")
    else:
        return render_template("anonymous.html")
