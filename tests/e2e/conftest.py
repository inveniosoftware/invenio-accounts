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


"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os
import shutil
import tempfile

import pytest
from flask import Flask
from flask_babelex import Babel
from flask_cli import FlaskCLI
from flask_mail import Mail
from flask_menu import Menu
from invenio_db import InvenioDB, db
from selenium import webdriver
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database

from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint


@pytest.fixture()
def app(request):
    """Flask application fixture for E2E/integration/selenium tests.

    Overrides the `app` fixture found in `../conftest.py`. Tests/files in
    this folder and subfolders will see this variant of the `app` fixture.
    """
    instance_path = tempfile.mkdtemp()
    app = Flask('testapp', instance_path=instance_path)
    app.config.update(
        ACCOUNTS_USE_CELERY=False,
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND="memory",
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND="cache",
        MAIL_SUPPRESS_SEND=True,
        SECRET_KEY="CHANGE_ME",
        SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        TESTING=True,
        LOGIN_DISABLED=False,
    )
    FlaskCLI(app)
    Menu(app)
    Babel(app)
    Mail(app)
    InvenioDB(app)
    InvenioAccounts(app)
    app.register_blueprint(blueprint)

    with app.app_context():
        if not database_exists(str(db.engine.url)):
            create_database(str(db.engine.url))
        db.create_all()

    def teardown():
        with app.app_context():
            drop_database(str(db.engine.url))
        shutil.rmtree(instance_path)

    request.addfinalizer(teardown)
    return app


@pytest.fixture()
def ff_browser(request):
    """Pytest fixture for a selenium/webdriver instance with Firefox."""
    ff = webdriver.Firefox()
    request.addfinalizer(lambda: ff.quit())
    return ff
