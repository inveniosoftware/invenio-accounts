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


"""Minimal Flask application example for development.

Create database and tables:

.. code-block:: console

   $ cd examples
   $ flask -a app.py db init
   $ flask -a app.py db create

Create a user:

.. code-block:: console

   $ flask -a app.py accounts usercreate -e info@invenio-software.org -a
   $ flask -a app.py accounts useractivate -u info@invenio-software.org

Run the development server:

   $ flask -a app.py --debug run --debugger
   $ flask -a app.py shell
"""

from __future__ import absolute_import, print_function

from flask import Flask, render_template
from flask_babelex import Babel
from flask_cli import FlaskCLI
from flask_mail import Mail
from flask_security import current_user
from invenio_db import InvenioDB

from invenio_accounts import InvenioAccounts

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
FlaskCLI(app)
Babel(app)
Mail(app)
InvenioDB(app)
InvenioAccounts(app)


@app.route("/")
def index():
    """Basic test view."""
    if current_user.is_authenticated():
        return render_template("authenticated.html")
    else:
        return render_template("anonymous.html")

if __name__ == "__main__":
    app.run()
