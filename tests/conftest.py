# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Pytest configuration."""

import os
import shutil
import tempfile

import pytest
from flask import Flask
from flask_admin import Admin
from flask_celeryext import FlaskCeleryExt
from flask_mail import Mail
from flask_menu import Menu
from invenio_db import InvenioDB, db
from invenio_i18n import Babel, InvenioI18N
from invenio_rest import InvenioREST
from simplekv.memory.redisstore import RedisStore
from sqlalchemy_utils.functions import create_database, database_exists, drop_database

from invenio_accounts import InvenioAccounts, InvenioAccountsREST
from invenio_accounts.admin import role_adminview, session_adminview, user_adminview
from invenio_accounts.testutils import create_test_user
from invenio_accounts.views.rest import create_blueprint


def _app_factory(config=None):
    """Application factory."""
    # TODO use the fixtures from pytest-invenio instead
    instance_path = tempfile.mkdtemp()
    app = Flask("testapp", instance_path=instance_path)
    icons = {
        "semantic-ui": {
            "key": "key icon",
            "link": "linkify icon",
            "shield": "shield alternate icon",
            "user": "user icon",
            "codepen": "codepen icon",
            "cogs": "cogs icon",
            "*": "{} icon",
        },
        "bootstrap3": {
            "key": "fa fa-key fa-fw",
            "link": "fa fa-link fa-fw",
            "shield": "fa fa-shield fa-fw",
            "user": "fa fa-user fa-fw",
            "codepen": "fa fa-codepen fa-fw",
            "cogs": "fa fa-cogs fa-fw",
            "*": "fa fa-{} fa-fw",
        },
    }

    app.config.update(
        ACCOUNTS_USE_CELERY=False,
        ACCOUNTS_LOCAL_LOGIN_ENABLED=True,
        APP_THEME=["semantic-ui"],
        THEME_ICONS=icons,
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND="memory",
        CELERY_TASK_EAGER_PROPAGATES=True,
        CELERY_RESULT_BACKEND="cache",
        LOGIN_DISABLED=False,
        MAIL_SUPPRESS_SEND=True,
        SECRET_KEY="CHANGE_ME",
        SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
        SECURITY_CONFIRM_EMAIL_WITHIN="2 seconds",
        SECURITY_RESET_PASSWORD_WITHIN="2 seconds",
        SECURITY_CHANGEABLE=True,
        SECURITY_RECOVERABLE=True,
        SECURITY_REGISTERABLE=True,
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
        ),
        SERVER_NAME="example.com",
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )

    app.config.update(config or {})
    Menu(app)
    Babel(app)
    Mail(app)
    InvenioDB(app)
    InvenioI18N(app)

    def delete_user_from_cache(exception):
        """Delete user from `flask.g` when the request is tearing down.

        Flask-login==0.6.2 changed the way the user is saved i.e uses `flask.g`.
        Flask.g is pointing to the application context which is initialized per
        request. That said, `pytest-flask` is pushing an application context on each
        test initialization that causes problems as subsequent requests during a test
        are detecting the active application request and not popping it when the
        sub-request is tearing down. That causes the logged in user to remain cached
        for the whole duration of the test. To fix this, we add an explicit teardown
        handler that will pop out the logged in user in each request and it will force
        the user to be loaded each time.
        """
        from flask import g

        if "_login_user" in g:
            del g._login_user

    app.teardown_request(delete_user_from_cache)

    return app


def _database_setup(app, request):
    """Set up the database."""
    with app.app_context():
        if not database_exists(str(db.engine.url)):
            create_database(str(db.engine.url))
        db.create_all()

    def teardown():
        with app.app_context():
            if database_exists(str(db.engine.url)):
                drop_database(str(db.engine.url))
            # Delete sessions in kvsession store
            if hasattr(app, "kvsession_store") and isinstance(
                app.kvsession_store, RedisStore
            ):
                app.kvsession_store.redis.flushall()
        shutil.rmtree(app.instance_path)

    request.addfinalizer(teardown)
    return app


@pytest.fixture()
def base_app(request):
    """Flask application fixture."""
    app = _app_factory()
    _database_setup(app, request)
    yield app


@pytest.fixture()
def app(request):
    """Flask application fixture with Invenio Accounts."""
    app = _app_factory()
    app.config.update(ACCOUNTS_USERINFO_HEADERS=True)
    InvenioAccounts(app)

    from invenio_accounts.views.settings import blueprint

    app.register_blueprint(blueprint)

    _database_setup(app, request)
    yield app


@pytest.fixture()
def api(request):
    """Flask application fixture."""
    api_app = _app_factory(
        dict(
            SQLALCHEMY_DATABASE_URI=os.environ.get(
                "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
            ),
            SERVER_NAME="localhost",
            TESTING=True,
        )
    )

    InvenioREST(api_app)
    InvenioAccountsREST(api_app)
    api_app.register_blueprint(create_blueprint(api_app))

    _database_setup(api_app, request)

    yield api_app


@pytest.fixture()
def app_with_redis_url(request):
    """Flask application fixture with Invenio Accounts."""
    app = _app_factory(dict(ACCOUNTS_SESSION_REDIS_URL="redis://localhost:6379/0"))
    app.config.update(ACCOUNTS_USERINFO_HEADERS=True)
    InvenioAccounts(app)

    from invenio_accounts.views.settings import blueprint

    app.register_blueprint(blueprint)

    _database_setup(app, request)
    yield app


@pytest.fixture()
def app_with_flexible_registration(request):
    """Flask application fixture with Invenio Accounts."""
    from webargs import fields

    from invenio_accounts.views.rest import RegisterView, use_kwargs

    class MyRegisterView(RegisterView):
        post_args = {**RegisterView.post_args, "active": fields.Boolean(required=True)}

        @use_kwargs(post_args)
        def post(self, **kwargs):
            """Register a user."""
            return super(MyRegisterView, self).post(**kwargs)

    api_app = _app_factory()
    InvenioREST(api_app)
    InvenioAccountsREST(api_app)

    api_app.config["ACCOUNTS_REST_AUTH_VIEWS"]["register"] = MyRegisterView

    api_app.register_blueprint(create_blueprint(api_app))

    _database_setup(api_app, request)
    yield api_app


@pytest.fixture
def task_app(request):
    """Flask application with Celery enabled."""
    app = _app_factory(
        dict(
            ACCOUNTS_USE_CELERY=True,
            MAIL_SUPPRESS_SEND=True,
        )
    )
    FlaskCeleryExt(app)
    InvenioAccounts(app)
    _database_setup(app, request)
    return app


@pytest.fixture
def cookie_app(request):
    """Flask application  enabled."""
    app = _app_factory(
        dict(
            SESSION_COOKIE_SECURE=True,
            SESSION_COOKIE_DOMAIN="example.com",
        )
    )
    InvenioAccounts(app)
    _database_setup(app, request)
    return app


@pytest.fixture
def admin_view(app):
    """Admin view fixture."""
    assert isinstance(role_adminview, dict)
    assert isinstance(user_adminview, dict)
    assert isinstance(session_adminview, dict)

    assert "model" in role_adminview
    assert "modelview" in role_adminview
    assert "model" in user_adminview
    assert "modelview" in user_adminview
    assert "model" in session_adminview
    assert "modelview" in session_adminview

    admin = Admin(app, name="Test")

    user_adminview_copy = dict(user_adminview)
    user_model = user_adminview_copy.pop("model")
    user_view = user_adminview_copy.pop("modelview")
    admin.add_view(user_view(user_model, db.session, **user_adminview_copy))

    admin.add_view(
        session_adminview["modelview"](
            session_adminview["model"],
            db.session,
            category=session_adminview["category"],
        )
    )


@pytest.fixture()
def users(app):
    """Create users."""
    user1 = create_test_user(email="INFO@inveniosoftware.org", password="tester")
    user2 = create_test_user(email="info2@invenioSOFTWARE.org", password="tester2")

    return [
        {
            "email": user1.email,
            "id": user1.id,
            "password": user1.password_plaintext,
            "obj": user1,
        },
        {
            "email": user2.email,
            "id": user2.id,
            "password": user2.password_plaintext,
            "obj": user2,
        },
    ]
