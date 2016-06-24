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


"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os
import shutil
import tempfile

import pytest
from flask import Flask
from flask_babelex import Babel
from flask_celeryext import FlaskCeleryExt
from flask_mail import Mail
from flask_menu import Menu
from invenio_db import InvenioDB, db
from simplekv.memory.redisstore import RedisStore
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database

from invenio_accounts import InvenioAccounts

try:
    from flask.cli import ScriptInfo
except ImportError:
    from flask_cli import ScriptInfo


def _app_factory(config=None):
    """Application factory."""
    instance_path = tempfile.mkdtemp()
    app = Flask('testapp', instance_path=instance_path)
    app.config.update(
        ACCOUNTS_USE_CELERY=False,
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND="memory",
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND="cache",
        LOGIN_DISABLED=False,
        MAIL_SUPPRESS_SEND=True,
        SECRET_KEY="CHANGE_ME",
        SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SERVER_NAME='example.com',
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )
    app.config.update(config or {})
    if not hasattr(app, 'cli'):
        from flask_cli import FlaskCLI
        FlaskCLI(app)
    Menu(app)
    Babel(app)
    Mail(app)
    InvenioDB(app)
    return app


def _database_setup(app, request):
    """Setup database."""
    with app.app_context():
        if not database_exists(str(db.engine.url)):
            create_database(str(db.engine.url))
        db.create_all()

    def teardown():
        with app.app_context():
            drop_database(str(db.engine.url))
            # Delete sessions in kvsession store
            if hasattr(app, 'kvsession_store') and \
                    isinstance(app.kvsession_store, RedisStore):
                app.kvsession_store.redis.flushall()
        shutil.rmtree(app.instance_path)

    request.addfinalizer(teardown)
    return app


@pytest.fixture
def base_app(request):
    """Flask application fixture."""
    app = _app_factory()
    _database_setup(app, request)
    return app


@pytest.fixture
def app(request):
    """Flask application fixture with Invenio Accounts."""
    app = _app_factory()
    InvenioAccounts(app)

    from invenio_accounts.views import blueprint
    app.register_blueprint(blueprint)

    _database_setup(app, request)
    return app


@pytest.fixture
def script_info(app):
    """Get ScriptInfo object for testing CLI."""
    return ScriptInfo(create_app=lambda info: app)


@pytest.fixture
def task_app(request):
    """Flask application with Celery enabled."""
    app = _app_factory(dict(
        ACCOUNTS_USE_CELERY=True,
        MAIL_SUPPRESS_SEND=True,
    ))
    FlaskCeleryExt(app)
    InvenioAccounts(app)
    _database_setup(app, request)
    return app
