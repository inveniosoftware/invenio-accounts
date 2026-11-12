# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-License-Identifier: MIT

"""Test that login and password reset do not disclose whether an account exists."""

import datetime
import json
from unittest import mock

from flask import url_for
from flask_security import url_for_security
from flask_security.signals import reset_password_instructions_sent
from flask_security.utils import get_message
from invenio_db import db

from invenio_accounts.testutils import create_test_user

LEAKY_MESSAGES = [
    "USER_DOES_NOT_EXIST",
    "INVALID_PASSWORD",
    "PASSWORD_NOT_SET",
    "CONFIRMATION_REQUIRED",
]


def _masked(response, email):
    """Return the response body, with the submitted email address masked."""
    return response.get_data(as_text=True).replace(email, "<email>")


def _assert_no_leaky_messages(body):
    for key in LEAKY_MESSAGES:
        assert get_message(key)[0] not in body


#
# UI
#
def test_login_ui_same_response_for_unknown_and_known_accounts(app):
    with app.app_context():
        create_test_user(email="normal@test.com")
        create_test_user(email="nopass@test.com", password=None)
        db.session.commit()

        attempts = {
            "unknown": ("unknown@test.com", "123456"),
            "wrong_password": ("normal@test.com", "wrong-password"),
            "no_password": ("nopass@test.com", "123456"),
        }
        bodies = {}
        with app.test_client() as client:
            for name, (email, password) in attempts.items():
                res = client.post(
                    url_for_security("login"),
                    data={"email": email, "password": password},
                )
                assert res.status_code == 200
                bodies[name] = _masked(res, email)

        generic = get_message("GENERIC_AUTHN_FAILED")[0]
        for body in bodies.values():
            assert generic in body
            _assert_no_leaky_messages(body)
        assert bodies["unknown"] == bodies["wrong_password"] == bodies["no_password"]


def test_login_ui_still_logs_in(app):
    with app.app_context():
        user = create_test_user(email="normal@test.com")
        db.session.commit()
        with app.test_client() as client:
            res = client.post(
                url_for_security("login"),
                data={"email": user.email, "password": user.password_plaintext},
            )
            assert res.status_code == 302


def test_forgot_password_ui_same_response_for_unknown_and_known_accounts(app):
    # Unconfirmed accounts are rejected by Flask-Security with their own error
    app.extensions["security"].login_without_confirmation = False

    with app.app_context():
        create_test_user(
            email="confirmed@test.com",
            confirmed_at=datetime.datetime.now(),
        )
        create_test_user(email="unconfirmed@test.com")
        db.session.commit()

        emails = {
            "confirmed": "confirmed@test.com",
            "unconfirmed": "unconfirmed@test.com",
            "unknown": "unknown@test.com",
        }
        bodies = {}
        recipients = []

        def _record(sender, user, token, **kwargs):
            recipients.append(user.email)

        with reset_password_instructions_sent.connected_to(_record, app):
            with app.test_client() as client:
                for name, email in emails.items():
                    res = client.post(
                        url_for_security("forgot_password"),
                        data={"email": email},
                    )
                    assert res.status_code == 200
                    bodies[name] = _masked(res, email)

        message = get_message("PASSWORD_RESET_REQUEST", email="<email>")[0]
        for body in bodies.values():
            assert message in body
            _assert_no_leaky_messages(body)
        assert bodies["confirmed"] == bodies["unconfirmed"] == bodies["unknown"]

        # Instructions are only sent to the account that can use them
        assert recipients == ["confirmed@test.com"]


def test_forgot_password_ui_rejects_invalid_email(app):
    with app.app_context():
        with app.test_client() as client:
            res = client.post(
                url_for_security("forgot_password"),
                data={"email": "not-an-email"},
            )
            body = res.get_data(as_text=True)
            assert res.status_code == 200
            assert get_message("INVALID_EMAIL_ADDRESS")[0] in body
            assert (
                get_message("PASSWORD_RESET_REQUEST", email="not-an-email")[0]
                not in body
            )


#
# REST API
#
def _json(response):
    return json.loads(response.get_data(as_text=True))


def test_login_rest_same_response_for_unknown_and_known_accounts(api):
    with api.app_context():
        create_test_user(email="normal@test.com")
        create_test_user(email="nopass@test.com", password=None)
        db.session.commit()

        attempts = {
            "unknown": ("unknown@test.com", "123456"),
            "wrong_password": ("normal@test.com", "wrong-password"),
            "no_password": ("nopass@test.com", "123456"),
        }
        responses = {}
        with api.test_client() as client:
            for name, (email, password) in attempts.items():
                res = client.post(
                    url_for("invenio_accounts_rest_auth.login"),
                    data={"email": email, "password": password},
                )
                responses[name] = (res.status_code, _json(res))

        expected = (
            400,
            {"status": 400, "message": get_message("GENERIC_AUTHN_FAILED")[0]},
        )
        assert responses["unknown"] == expected
        assert responses["wrong_password"] == expected
        assert responses["no_password"] == expected


def test_forgot_password_rest_same_response_for_unknown_and_known_accounts(api):
    with api.app_context():
        create_test_user(email="normal@test.com")
        db.session.commit()

        recipients = []

        def _send_mail(subject, recipient, template, **context):
            recipients.append(recipient)

        with mock.patch("invenio_accounts.views.rest.send_mail", _send_mail):
            with api.test_client() as client:
                url = url_for("invenio_accounts_rest_auth.forgot_password")
                known = client.post(url, data={"email": "normal@test.com"})
                unknown = client.post(url, data={"email": "unknown@test.com"})

        assert known.status_code == unknown.status_code == 200
        assert _masked(known, "normal@test.com") == _masked(unknown, "unknown@test.com")
        assert _json(known)["message"] == (
            get_message("PASSWORD_RESET_REQUEST", email="normal@test.com")[0]
        )
        assert recipients == ["normal@test.com"]
