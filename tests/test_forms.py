# SPDX-FileCopyrightText: 2016-2018 CERN.
# SPDX-License-Identifier: MIT

"""Test forms."""

from flask_security.forms import ConfirmRegisterForm, RegisterForm

from invenio_accounts.forms import confirm_register_form_factory, register_form_factory


def test_confirm_register_form_factory(app):
    """Test factory."""
    form = confirm_register_form_factory(ConfirmRegisterForm, app)
    assert not hasattr(form, "recaptcha")
    app.config.update(
        dict(
            RECAPTCHA_PUBLIC_KEY="test",
            RECAPTCHA_PRIVATE_KEY="test",
        )
    )
    form = confirm_register_form_factory(ConfirmRegisterForm, app)
    assert hasattr(form, "recaptcha")


def test_register_form_factory(app):
    """Test factory."""
    form = register_form_factory(RegisterForm, app)
    assert not hasattr(form, "recaptcha")
    app.config.update(
        dict(
            RECAPTCHA_PUBLIC_KEY="test",
            RECAPTCHA_PRIVATE_KEY="test",
        )
    )
    form = register_form_factory(RegisterForm, app)
    assert hasattr(form, "recaptcha")
