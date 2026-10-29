# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-License-Identifier: MIT

"""Test re-authentication with a code sent by email."""

import re
from datetime import timedelta

import pytest
from flask import url_for
from invenio_app.ext import InvenioApp

from invenio_accounts.reauth import (
    SESSION_REAUTH_AT_KEY,
    SESSION_REAUTH_CODE_KEY,
)
from invenio_accounts.testutils import create_test_user, login_user_via_session


@pytest.fixture()
def client(reauth_app):
    """Logged-in test client."""
    with reauth_app.app_context():
        user = create_test_user(email="user@example.org")
        with reauth_app.test_client() as client:
            login_user_via_session(client, user=user)
            yield client


def _send_code(app, client):
    with app.extensions["mail"].record_messages() as outbox:
        res = client.post(url_for("invenio_accounts.reauth"), data={"action": "send"})
        assert res.status_code == 302
    assert len(outbox) == 1
    return re.search(r"\b(\d{6})\b", outbox[0].body).group(1)


def _verify(client, code, next_url="/protected"):
    return client.post(
        url_for("invenio_accounts.reauth", next=next_url),
        data={"action": "verify", "verify-code": code},
    )


def test_protected_view_redirects_to_reauth(reauth_app, client):
    res = client.get("/protected")
    assert res.status_code == 302
    assert url_for("invenio_accounts.reauth", next="/protected") in res.location

    # POST is not processed either
    res = client.post("/protected")
    assert res.status_code == 302
    assert "/account/settings/reauth" in res.location


def test_methods_restriction(reauth_app, client):
    assert client.get("/protected-post").status_code == 200
    assert client.post("/protected-post").status_code == 302


def test_full_flow(reauth_app, client):
    code = _send_code(reauth_app, client)
    res = _verify(client, code)
    assert res.status_code == 302
    assert res.location.endswith("/protected")

    assert client.get("/protected").get_data(as_text=True) == "protected"
    assert client.post("/protected").status_code == 200

    # the code can only be used once
    with client.session_transaction() as sess:
        assert SESSION_REAUTH_CODE_KEY not in sess


def test_window_expires(reauth_app, client):
    code = _send_code(reauth_app, client)
    _verify(client, code)
    assert client.get("/protected").status_code == 200

    with client.session_transaction() as sess:
        data = sess[SESSION_REAUTH_AT_KEY]
        data["at"] -= reauth_app.config["ACCOUNTS_REAUTH_WINDOW"].total_seconds() + 1
        sess[SESSION_REAUTH_AT_KEY] = data
    assert client.get("/protected").status_code == 302


def test_wrong_code(reauth_app, client):
    code = _send_code(reauth_app, client)
    wrong = "000000" if code != "000000" else "111111"
    res = _verify(client, wrong)
    assert res.status_code == 200
    assert "invalid or has expired" in res.get_data(as_text=True)
    assert client.get("/protected").status_code == 302

    # the right code still works after a wrong attempt
    assert _verify(client, code).status_code == 302
    assert client.get("/protected").status_code == 200


def test_max_attempts_invalidates_code(reauth_app, client):
    code = _send_code(reauth_app, client)
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(reauth_app.config["ACCOUNTS_REAUTH_MAX_ATTEMPTS"]):
        _verify(client, wrong)
    assert _verify(client, code).status_code == 200
    assert client.get("/protected").status_code == 302


def test_expired_code(reauth_app, client):
    code = _send_code(reauth_app, client)
    with client.session_transaction() as sess:
        data = sess[SESSION_REAUTH_CODE_KEY]
        data["expires"] -= reauth_app.config["ACCOUNTS_REAUTH_CODE_TTL"].total_seconds()
        sess[SESSION_REAUTH_CODE_KEY] = data
    assert _verify(client, code).status_code == 200
    assert client.get("/protected").status_code == 302


def test_code_not_stored_in_clear(reauth_app, client):
    code = _send_code(reauth_app, client)
    with client.session_transaction() as sess:
        assert code not in str(sess[SESSION_REAUTH_CODE_KEY])


def test_external_next_is_rejected(reauth_app, client):
    code = _send_code(reauth_app, client)
    for next_url in ["https://evil.org/", "//evil.org/", "/\\evil.org"]:
        res = _verify(client, code, next_url=next_url)
        assert res.location in ("/", "http://example.com/")
        code = _send_code(reauth_app, client)


def test_reauth_bound_to_user(reauth_app, client):
    code = _send_code(reauth_app, client)
    _verify(client, code)

    other = create_test_user(email="other@example.org")
    login_user_via_session(client, user=other)
    assert client.get("/protected").status_code == 302


def test_user_without_email_is_refused(reauth_app, client):
    from invenio_db import db

    from invenio_accounts.models import User

    user = User.query.filter_by(email="user@example.org").one()
    user._email = None
    db.session.commit()

    with reauth_app.extensions["mail"].record_messages() as outbox:
        client.post(url_for("invenio_accounts.reauth"), data={"action": "send"})
    assert outbox == []
    assert client.get("/protected").status_code == 302


def test_send_rate_limit(reauth_app, client):
    reauth_app.config["ACCOUNTS_REAUTH_SEND_RATELIMIT"] = "1 per minute"
    InvenioApp(reauth_app)

    _send_code(reauth_app, client)
    with reauth_app.extensions["mail"].record_messages() as outbox:
        client.post(url_for("invenio_accounts.reauth"), data={"action": "send"})
    assert outbox == []


def test_disabled_is_passthrough(reauth_app, client):
    reauth_app.config["ACCOUNTS_REAUTH_ENABLED"] = False
    assert client.get("/protected").status_code == 200


def test_reauth_page_when_fresh_redirects(reauth_app, client):
    code = _send_code(reauth_app, client)
    _verify(client, code)
    res = client.get(url_for("invenio_accounts.reauth", next="/protected"))
    assert res.status_code == 302
    assert res.location.endswith("/protected")


def test_reauth_page_renders(reauth_app, client):
    res = client.get(url_for("invenio_accounts.reauth", next="/protected"))
    assert res.status_code == 200
    assert "user@example.org" in res.get_data(as_text=True)


def test_route_not_registered_when_disabled(app):
    assert "invenio_accounts.reauth" not in app.view_functions


def test_window_config_is_timedelta(app):
    assert isinstance(app.config["ACCOUNTS_REAUTH_WINDOW"], timedelta)


def test_post_redirects_back_to_local_referrer(reauth_app, client):
    res = client.post("/protected", headers={"Referer": "http://example.com/form?a=1"})
    assert url_for("invenio_accounts.reauth", next="/form?a=1") in res.location

    res = client.post("/protected", headers={"Referer": "https://evil.org/form"})
    assert url_for("invenio_accounts.reauth", next="/") in res.location

    res = client.post("/protected")
    assert url_for("invenio_accounts.reauth", next="/") in res.location
