# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Additional non-userprofile fields used during registration.

Currently supported: recaptcha
"""
from flask_babelex import gettext as _
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
    if app.config.get('RECAPTCHA_PUBLIC_KEY') and \
            app.config.get('RECAPTCHA_PRIVATE_KEY'):
        class ConfirmRegisterForm(Form):
            recaptcha = FormField(RegistrationFormRecaptcha, separator='.')

        return ConfirmRegisterForm

    return Form


def register_form_factory(Form, app):
    """Return extended registration form."""
    if app.config.get('RECAPTCHA_PUBLIC_KEY') and \
            app.config.get('RECAPTCHA_PRIVATE_KEY'):
        class RegisterForm(Form):
            recaptcha = FormField(RegistrationFormRecaptcha, separator='.')

        return RegisterForm

    return Form
