# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Accounts utils."""

from datetime import timedelta

from flask import render_template

from invenio_base.globals import cfg
from invenio_base.i18n import _
from invenio.ext.email import send_email

from .errors import AccountSecurityError
from .tokens import EmailConfirmationSerializer


def send_reset_password_email(email):
    """Reset password by sending a email with the unique link."""
    expires_in = cfg.get('CFG_WEBSESSION_ADDRESS_ACTIVATION_EXPIRE_IN_DAYS')

    reset_key = EmailConfirmationSerializer(
        expires_in=timedelta(days=expires_in).total_seconds()
    ).create_token(email, {'email': email})

    if not reset_key:
        raise AccountSecurityError(
            _('Something goes wrong when the cookie has been generated')
        )

    email_text = render_template(
        'accounts/email_reset_password.html',
        reset_key=reset_key, email=email
    )

    return send_email(
        fromaddr=cfg['CFG_SITE_SUPPORT_EMAIL'],
        subject=_("Password reset request for %(website)s",
                  website=cfg['CFG_SITE_URL']),
        toaddr=email,
        content=email_text
    )
