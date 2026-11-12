# SPDX-FileCopyrightText: 2016-2026 CERN.
# SPDX-License-Identifier: MIT

"""Additional non-userprofile fields used during registration.

Currently supported: recaptcha
"""

from flask import request
from flask_security.forms import NextFormMixin
from flask_security.utils import get_message
from flask_wtf import FlaskForm, Recaptcha, RecaptchaField
from invenio_db import db
from invenio_i18n import gettext as _
from wtforms import FormField, HiddenField

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


def _remove_errors(field, message_keys):
    """Remove the given Flask-Security messages from a field's errors.

    :returns: ``True`` if any error was removed.
    """
    messages = {get_message(key)[0] for key in message_keys}
    remaining = [error for error in field.errors if error not in messages]
    removed = len(remaining) != len(field.errors)
    field.errors = remaining
    return removed


def login_form_factory(Form, app):
    """Return extended login form.

    Flask-Security reports an unknown email address, an account without a
    password and a wrong password with different errors on different fields,
    which discloses whether an account exists. These are replaced by a single
    form-level error.
    """

    class LoginForm(Form):
        def validate(self, extra_validators=None):
            is_valid = super().validate(extra_validators=extra_validators)
            if not is_valid:
                concealed_email = _remove_errors(self.email, ["USER_DOES_NOT_EXIST"])
                concealed_password = _remove_errors(
                    self.password, ["PASSWORD_NOT_SET", "INVALID_PASSWORD"]
                )
                if concealed_email or concealed_password:
                    self.form_errors = [
                        *self.form_errors,
                        get_message("GENERIC_AUTHN_FAILED")[0],
                    ]
            if app.config.get("ACCOUNTS_LOGIN_RATELIMIT"):
                allowed, message = enforce_login_limit(self.email.data)
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
    """Return forgot-password form that does not disclose account existence.

    Flask-Security rejects unknown and unconfirmed email addresses with
    validation errors, which discloses whether an account exists. This form
    accepts them instead, with ``user`` set to ``None`` so that no
    instructions are sent. It must be used together with
    :func:`invenio_accounts.views.settings.forgot_password`, which shows the
    same message in both cases.

    The form also applies the per-account rate limit
    (``ACCOUNTS_FORGOT_PASSWORD_EMAIL_RATELIMIT``), if configured.
    """

    class ForgotPasswordForm(Form):
        def validate(self, extra_validators=None):
            if not super().validate(extra_validators=extra_validators):
                concealed = _remove_errors(
                    self.email, ["USER_DOES_NOT_EXIST", "CONFIRMATION_REQUIRED"]
                )
                if not concealed or self.errors:
                    # Any other error, e.g. an invalid email address or CSRF token
                    return False
                self.user = None

            allowed, message = enforce_forgot_password_limit(self.email.data)
            if not allowed:
                self.email.errors = [*self.email.errors, str(message)]
                return False
            return True

    return ForgotPasswordForm
