# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Additional non-userprofile fields used during registration.

Currently supported: recaptcha
"""
from flask import request
from flask_babelex import gettext as _
from flask_security.forms import NextFormMixin
from flask_wtf import FlaskForm, Recaptcha, RecaptchaField
from wtforms import FormField, HiddenField


class RegistrationFormRecaptcha(FlaskForm):
    """Form for editing user profile."""

    recaptcha = RecaptchaField(validators=[
        Recaptcha(message=_("Please complete the reCAPTCHA."))])


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
                self.next.data = request.args.get('next', '')

    if app.config.get('RECAPTCHA_PUBLIC_KEY') and \
            app.config.get('RECAPTCHA_PRIVATE_KEY'):
        class ConfirmRegisterWithCaptchaForm(ConfirmRegisterForm):
            recaptcha = FormField(RegistrationFormRecaptcha, separator='.')

        return ConfirmRegisterWithCaptchaForm

    return ConfirmRegisterForm


def register_form_factory(Form, app):
    """Return extended registration form."""
    if app.config.get('RECAPTCHA_PUBLIC_KEY') and \
            app.config.get('RECAPTCHA_PRIVATE_KEY'):
        class RegisterForm(Form):
            recaptcha = FormField(RegistrationFormRecaptcha, separator='.')

        return RegisterForm

    return Form


def login_form_factory(Form, app):
    """Return extended login form."""
    class LoginForm(Form):

        def __init__(self, *args, **kwargs):
            """Init the login form.

            .. note::

                The ``remember me`` option will be completely disabled.
            """
            super(LoginForm, self).__init__(*args, **kwargs)
            self.remember.data = False

    return LoginForm
