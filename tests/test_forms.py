# SPDX-FileCopyrightText: 2016-2026 CERN.
# SPDX-License-Identifier: MIT

"""Test forms."""

import pytest
from flask_security.forms import ConfirmRegisterForm, RegisterForm

from invenio_accounts import InvenioAccounts
from invenio_accounts.forms import confirm_register_form_factory, register_form_factory

LEGACY_RECAPTCHA_CONFIG = dict(
    RECAPTCHA_PUBLIC_KEY="test",
    RECAPTCHA_PRIVATE_KEY="test",
)


@pytest.mark.parametrize(
    "factory,form",
    [
        (register_form_factory, RegisterForm),
        (confirm_register_form_factory, ConfirmRegisterForm),
    ],
)
def test_legacy_recaptcha_config_enables_altcha(app, factory, form):
    """Deprecated reCAPTCHA keys transparently enable ALTCHA."""
    assert not hasattr(factory(form, app), "altcha")
    assert not hasattr(factory(form, app), "recaptcha")

    app.config.update(LEGACY_RECAPTCHA_CONFIG)
    form_class = factory(form, app)
    assert hasattr(form_class, "altcha")

    # Templates written for reCAPTCHA keep rendering a captcha.
    with app.test_request_context():
        instance = form_class(meta={"csrf": False})
        assert instance.recaptcha is instance.altcha


def test_legacy_recaptcha_config_warns(base_app, caplog):
    """A deprecation warning is emitted for the reCAPTCHA keys."""
    base_app.config.update(LEGACY_RECAPTCHA_CONFIG)
    with pytest.warns(DeprecationWarning, match="ACCOUNTS_ALTCHA_ENABLED"):
        InvenioAccounts(base_app)
    assert "privacy-friendly" in caplog.text


def test_no_warning_without_legacy_config(base_app, recwarn):
    """No deprecation warning without the reCAPTCHA keys."""
    base_app.config["ACCOUNTS_ALTCHA_ENABLED"] = True
    InvenioAccounts(base_app)
    assert not [
        w for w in recwarn if "reCAPTCHA" in str(w.message)
    ], "unexpected reCAPTCHA warning"
