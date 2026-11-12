# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-License-Identifier: MIT

"""Test ALTCHA captcha on registration."""

import pytest
from altcha import Challenge, Payload, solve_challenge
from flask import url_for
from flask_security import url_for_security
from flask_security.forms import ConfirmRegisterForm, RegisterForm
from invenio_app.ext import InvenioApp

from invenio_accounts import InvenioAccounts
from invenio_accounts.forms import confirm_register_form_factory, register_form_factory
from invenio_accounts.models import User
from invenio_accounts.views.settings import create_settings_blueprint


@pytest.fixture()
def altcha_app(base_app):
    """Application with ALTCHA enabled."""
    base_app.config.update(
        ACCOUNTS_ALTCHA_ENABLED=True,
        # Keep the proof-of-work cheap in tests.
        ACCOUNTS_ALTCHA_ALGORITHM="SHA-256",
        ACCOUNTS_ALTCHA_COST=1,
    )
    InvenioAccounts(base_app)
    base_app.register_blueprint(create_settings_blueprint(base_app))
    with base_app.app_context():
        yield base_app


def _solve(client):
    """Fetch a challenge from the server and solve it like the widget does."""
    resp = client.get(url_for("invenio_accounts.altcha_challenge"))
    assert resp.status_code == 200
    assert resp.headers["Cache-Control"] == "no-store"
    challenge = Challenge.from_dict(resp.get_json())
    return Payload(challenge, solve_challenge(challenge)).to_base64()


def _register(client, email, altcha=None):
    data = dict(email=email, password="test1234")
    if altcha is not None:
        data["altcha"] = altcha
    return client.post(url_for_security("register"), data=data)


def test_form_factories(app, altcha_app):
    """Field is only added when ALTCHA is enabled."""
    for factory, form in [
        (register_form_factory, RegisterForm),
        (confirm_register_form_factory, ConfirmRegisterForm),
    ]:
        assert not hasattr(factory(form, app), "altcha")
        assert hasattr(factory(form, altcha_app), "altcha")


def test_challenge_endpoint_disabled(app):
    """Challenge endpoint does not exist when ALTCHA is disabled."""
    with app.test_request_context():
        assert "invenio_accounts.altcha_challenge" not in app.view_functions


def test_widget_rendered(altcha_app):
    """Registration page renders the widget."""
    with altcha_app.test_client() as client:
        html = client.get(url_for_security("register")).get_data(as_text=True)
        assert "<altcha-widget" in html
        assert 'challenge="/account/settings/altcha/challenge"' in html
        assert altcha_app.config["ACCOUNTS_ALTCHA_WIDGET_URL"] in html


def test_registration_requires_altcha(altcha_app):
    """Registration fails without a valid solution."""
    with altcha_app.test_client() as client:
        for altcha in [None, "", "not-base64!", "e30="]:
            resp = _register(client, "a@example.org", altcha)
            assert "Please complete the verification" in resp.get_data(as_text=True)
    with altcha_app.app_context():
        assert User.query.count() == 0


def test_registration_with_altcha(altcha_app):
    """Registration succeeds with a valid solution."""
    with altcha_app.test_client() as client:
        resp = _register(client, "a@example.org", _solve(client))
        assert resp.status_code == 302
    with altcha_app.app_context():
        assert User.query.filter_by(email="a@example.org").one()


def test_tampered_challenge_rejected(altcha_app):
    """A challenge signed with another key is rejected."""
    with altcha_app.test_client() as client:
        payload = _solve(client)
        altcha_app.config["ACCOUNTS_ALTCHA_HMAC_KEY"] = "another-key"
        resp = _register(client, "a@example.org", payload)
        assert "Please complete the verification" in resp.get_data(as_text=True)


def test_expired_challenge_rejected(altcha_app):
    """An expired challenge is rejected."""
    from datetime import timedelta

    altcha_app.config["ACCOUNTS_ALTCHA_EXPIRES"] = timedelta(seconds=-1)
    with altcha_app.test_client() as client:
        resp = _register(client, "a@example.org", _solve(client))
        assert "Please complete the verification" in resp.get_data(as_text=True)


def test_replay_rejected(altcha_app):
    """A solved challenge can only be used once."""
    altcha_app.config.update(
        APP_ENABLE_SECURE_HEADERS=False, RATELIMIT_STORAGE_URI="memory://"
    )
    InvenioApp(altcha_app)
    with altcha_app.test_client() as client:
        payload = _solve(client)
        assert _register(client, "a@example.org", payload).status_code == 302
    # Replay from another (anonymous) client.
    with altcha_app.test_client() as client:
        resp = _register(client, "b@example.org", payload)
        assert "Please complete the verification" in resp.get_data(as_text=True)
    with altcha_app.app_context():
        assert User.query.filter_by(email="b@example.org").count() == 0


def test_legacy_recaptcha_config(base_app):
    """Deprecated reCAPTCHA keys protect registration with ALTCHA."""
    base_app.config.update(
        RECAPTCHA_PUBLIC_KEY="test",
        RECAPTCHA_PRIVATE_KEY="test",
        ACCOUNTS_ALTCHA_ALGORITHM="SHA-256",
        ACCOUNTS_ALTCHA_COST=1,
    )
    with pytest.warns(DeprecationWarning):
        InvenioAccounts(base_app)
    base_app.register_blueprint(create_settings_blueprint(base_app))
    with base_app.app_context(), base_app.test_client() as client:
        html = client.get(url_for_security("register")).get_data(as_text=True)
        assert "<altcha-widget" in html
        resp = _register(client, "a@example.org")
        assert "Please complete the verification" in resp.get_data(as_text=True)
        assert _register(client, "a@example.org", _solve(client)).status_code == 302
