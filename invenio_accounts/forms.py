# SPDX-FileCopyrightText: 2016-2026 CERN.
# SPDX-License-Identifier: MIT

"""Additional non-userprofile fields used during registration.

Currently supported: recaptcha
"""

from flask import request
from flask_security.forms import NextFormMixin
from flask_wtf import FlaskForm, Recaptcha, RecaptchaField
from invenio_db import db
from invenio_i18n import lazy_gettext as _
from wtforms import FormField, HiddenField, StringField
from wtforms.validators import DataRequired, Regexp

from .limiter import (
    enforce_forgot_password_limit,
    enforce_login_limit,
    enforce_send_confirmation_limit,
)
from .proxies import current_datastore
from .utils import validate_domain


class RegistrationFormRecaptcha(FlaskForm):
    """Form for editing user profile."""

    recaptcha = RecaptchaField(
        validators=[Recaptcha(message=_("Please complete the reCAPTCHA."))]
    )


class RevokeForm(FlaskForm):
    """Form for revoking a session."""

    sid_s = HiddenField()


class ReauthSendCodeForm(FlaskForm):
    """Form for requesting a re-authentication code."""


class ReauthVerifyCodeForm(FlaskForm):
    """Form for entering a re-authentication code."""

    code = StringField(
        _("Verification code"),
        validators=[
            DataRequired(),
            Regexp(r"^\s*\d{6}\s*$", message=_("Enter the 6-digit code.")),
        ],
        render_kw={"autocomplete": "one-time-code", "inputmode": "numeric"},
    )


def confirm_register_form_factory(Form, app):
    """Return confirmation for extended registration form."""

    class ConfirmRegisterForm(Form, NextFormMixin):
        def __init__(self, *args, **kwargs):
            """Adds next parameter from URL."""
            super(ConfirmRegisterForm, self).__init__(*args, **kwargs)
            if not self.next.data:
                self.next.data = request.args.get("next", "")

        def validate(self, extra_validators=None):
            """Validate domain on email list."""
            if not super().validate(extra_validators=extra_validators):
                return False

            if not validate_domain(self.email.data):
                self.email.errors.append(_("The email domain is blocked."))
                return False
            return True

    if app.config.get("RECAPTCHA_PUBLIC_KEY") and app.config.get(
        "RECAPTCHA_PRIVATE_KEY"
    ):

        class ConfirmRegisterWithCaptchaForm(ConfirmRegisterForm):
            recaptcha = FormField(RegistrationFormRecaptcha, separator=".")

        return ConfirmRegisterWithCaptchaForm

    return ConfirmRegisterForm


def register_form_factory(Form, app):
    """Return extended registration form."""
    if app.config.get("RECAPTCHA_PUBLIC_KEY") and app.config.get(
        "RECAPTCHA_PRIVATE_KEY"
    ):

        class RegisterForm(Form):
            recaptcha = FormField(RegistrationFormRecaptcha, separator=".")

        return RegisterForm

    return Form


def login_form_factory(Form, app):
    """Return extended login form."""

    class LoginForm(Form):
        def validate(self, extra_validators=None):
            is_valid = super().validate(extra_validators=extra_validators)
            if app.config.get("ACCOUNTS_LOGIN_RATELIMIT"):
                allowed, message = enforce_login_limit(getattr(self, "user", None))
                if not allowed:
                    self.form_errors = [*self.form_errors, str(message)]
                    self.email.errors = []
                    self.password.errors = []
                    return False
            return is_valid

    return LoginForm


def send_confirmation_form_factory(Form, app):
    """Return extended login form."""

    class SendConfirmationEmailView(Form):
        """Form which sends confirmation instructions.

        If user not in the system, do not raise but ignore.
        The overriden behaviour exists because the endpoint is public and users can
        take an insight on which emails exist in the system otherwise.
        """

        def validate(self, extra_validators=None):
            with db.session.no_autoflush:
                self.user = current_datastore.get_user(self.data["email"])
            # Form is valid if user exists and they are not yet confirmed
            if self.user is not None and self.user.confirmed_at is None:
                if app.config.get("ACCOUNTS_SEND_CONFIRMATION_RATELIMIT"):
                    allowed, message = enforce_send_confirmation_limit(self.user)
                    if not allowed:
                        self.email.errors = [*self.email.errors, str(message)]
                        return False
                return True
            return False

    return SendConfirmationEmailView


def forgot_password_form_factory(Form, app):
    """Return forgot-password form with per-account rate limiting."""

    class ForgotPasswordForm(Form):
        def validate(self, extra_validators=None):
            if not super().validate(extra_validators=extra_validators):
                return False
            allowed, message = enforce_forgot_password_limit(self.user)
            if not allowed:
                self.email.errors = [*self.email.errors, str(message)]
                return False
            return True

    return ForgotPasswordForm
