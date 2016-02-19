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

"""Test forms."""

from __future__ import absolute_import, print_function

from flask_security.forms import ConfirmRegisterForm, RegisterForm

from invenio_accounts.forms import confirm_register_form_factory, \
    register_form_factory


def test_confirm_register_form_factory(app):
    """Test factory."""
    form = confirm_register_form_factory(ConfirmRegisterForm, app)
    assert not hasattr(form, 'recaptcha')
    app.config.update(dict(
        RECAPTCHA_PUBLIC_KEY='test',
        RECAPTCHA_PRIVATE_KEY='test',
    ))
    form = confirm_register_form_factory(ConfirmRegisterForm, app)
    assert hasattr(form, 'recaptcha')


def test_register_form_factory(app):
    """Test factory."""
    form = register_form_factory(RegisterForm, app)
    assert not hasattr(form, 'recaptcha')
    app.config.update(dict(
        RECAPTCHA_PUBLIC_KEY='test',
        RECAPTCHA_PRIVATE_KEY='test',
    ))
    form = register_form_factory(RegisterForm, app)
    assert hasattr(form, 'recaptcha')
