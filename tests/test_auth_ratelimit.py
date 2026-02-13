# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2026 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test per-account auth rate limits."""

from flask import url_for
from flask_security import url_for_security
from invenio_app.ext import InvenioApp
from invenio_db import db

from invenio_accounts.forms import forgot_password_form_factory
from invenio_accounts.testutils import create_test_user


def _init_limiter(app, forgot_password_limit=None, **config):
    app.config.update(
        APP_ENABLE_SECURE_HEADERS=False,
        RATELIMIT_STORAGE_URI="memory://",
        **config,
    )
    if forgot_password_limit is not None:
        app.config["ACCOUNTS_FORGOT_PASSWORD_EMAIL_RATELIMIT"] = forgot_password_limit
        app.extensions["security"].forgot_password_form = forgot_password_form_factory(
            app.extensions["security"].forgot_password_form,
            app,
        )
    InvenioApp(app)

    @app.errorhandler(429)
    def _too_many_requests(error):
        return str(error.description), 429


def test_forgot_password_per_account_limit_blocks_second_request_same_email(app):
    _init_limiter(app, forgot_password_limit="1 per minute")

    with app.app_context():
        create_test_user(email="normal@test.com")
        with app.test_client() as client:
            url = url_for_security("forgot_password")
            first = client.post(
                url,
                data={"email": "NORMAL@TEST.COM"},
            )
            second = client.post(
                url,
                data={"email": "normal@test.com"},
            )

            assert first.status_code != 429
            assert second.status_code == 200
            assert str(
                app.config["ACCOUNTS_FORGOT_PASSWORD_EMAIL_RATELIMIT_MSG"]
            ) in second.get_data(as_text=True)


def test_forgot_password_per_account_limit_allows_different_emails(app):
    _init_limiter(app, forgot_password_limit="1 per minute")

    with app.app_context():
        create_test_user(email="first@test.com")
        create_test_user(email="second@test.com")
        with app.test_client() as client:
            url = url_for_security("forgot_password")
            first = client.post(
                url,
                data={"email": "first@test.com"},
            )
            second = client.post(
                url,
                data={"email": "second@test.com"},
            )

            assert first.status_code != 429
            assert second.status_code != 429


def test_forgot_password_per_account_limit_disabled_by_default(app):
    _init_limiter(app)

    with app.app_context():
        create_test_user(email="normal@test.com")
        with app.test_client() as client:
            url = url_for_security("forgot_password")
            first = client.post(
                url,
                data={"email": "normal@test.com"},
            )
            second = client.post(
                url,
                data={"email": "normal@test.com"},
            )

            assert first.status_code != 429
            assert second.status_code != 429


def test_login_per_account_limit_blocks_second_attempt_ui(app):
    _init_limiter(app, ACCOUNTS_LOGIN_RATELIMIT="1 per minute")

    with app.app_context():
        user = create_test_user(email="normal@test.com")
        db.session.commit()
        with app.test_client() as client:
            url = url_for_security("login")
            first = client.post(
                url,
                data={"email": user.email, "password": "wrong-password"},
            )
            second = client.post(
                url,
                data={"email": user.email, "password": "wrong-password"},
            )

            assert first.status_code != 429
            assert second.status_code == 200
            assert str(app.config["ACCOUNTS_LOGIN_RATELIMIT_MSG"]) in second.get_data(
                as_text=True
            )
            assert "invalid password" not in second.get_data(as_text=True).lower()


def test_login_per_account_limit_blocks_second_attempt_rest(api):
    _init_limiter(api, ACCOUNTS_LOGIN_RATELIMIT="1 per minute")

    with api.app_context():
        user = create_test_user(email="normal@test.com")
        db.session.commit()
        with api.test_client() as client:
            url = url_for("invenio_accounts_rest_auth.login")
            first = client.post(
                url,
                data={"email": user.email, "password": "wrong-password"},
            )
            second = client.post(
                url,
                data={"email": user.email, "password": "wrong-password"},
            )

            assert first.status_code != 429
            assert second.status_code == 429
            assert second.get_data(as_text=True) == str(
                api.config["ACCOUNTS_LOGIN_RATELIMIT_MSG"]
            )


def test_send_confirmation_per_account_limit_blocks_second_attempt_ui(app):
    _init_limiter(app, ACCOUNTS_SEND_CONFIRMATION_RATELIMIT="1 per minute")

    with app.app_context():
        user = create_test_user(email="normal@test.com")
        db.session.commit()
        with app.test_client() as client:
            url = url_for_security("send_confirmation")
            first = client.post(
                url,
                data={"email": user.email},
            )
            second = client.post(
                url,
                data={"email": user.email},
            )

            assert first.status_code != 429
            assert second.status_code == 200
            assert str(
                app.config["ACCOUNTS_SEND_CONFIRMATION_RATELIMIT_MSG"]
            ) in second.get_data(as_text=True)


def test_send_confirmation_per_account_limit_blocks_second_attempt_rest(api):
    _init_limiter(api, ACCOUNTS_SEND_CONFIRMATION_RATELIMIT="1 per minute")

    with api.app_context():
        user = create_test_user(email="normal@test.com")
        db.session.commit()
        with api.test_client() as client:
            login_url = url_for("invenio_accounts_rest_auth.login")
            login = client.post(
                login_url,
                data={"email": user.email, "password": "123456"},
            )
            assert login.status_code == 200

            url = url_for("invenio_accounts_rest_auth.send_confirmation")
            first = client.post(
                url,
                data={"email": user.email},
            )
            second = client.post(
                url,
                data={"email": user.email},
            )

            assert first.status_code != 429
            assert second.status_code == 429
            assert second.get_data(as_text=True) == str(
                api.config["ACCOUNTS_SEND_CONFIRMATION_RATELIMIT_MSG"]
            )
