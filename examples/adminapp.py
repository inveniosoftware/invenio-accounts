# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
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


"""Minimal Flask application example for admin views.

Create database and tables:

.. code-block:: console

   $ cd examples
   $ export FLASK_APP=adminapp.py
   $ flask db init
   $ flask db create

Create some users:

.. code-block:: console

   $ flask users create info@inveniosoftware.org -a
   $ flask users create reader@inveniosoftware.org -a
   $ flask users create editor@inveniosoftware.org -a
   $ flask users create admin@inveniosoftware.org -a

Run the development server:

.. code-block:: console

   $ flask run

"""

from __future__ import absolute_import, print_function

import os

from flask import Flask
from flask_babelex import Babel
from flask_mail import Mail
from flask_menu import Menu
from invenio_admin import InvenioAdmin
from invenio_db import InvenioDB

from invenio_accounts import InvenioAccounts

app = Flask(__name__)
app.secret_key = 'ExampleApp'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'
)
Babel(app)
Mail(app)
Menu(app)
InvenioDB(app)
accounts = InvenioAccounts(app)


InvenioAdmin(app, permission_factory=lambda x: x,
             view_class_factory=lambda x: x)
