# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test token duration."""

import time

from flask_security import url_for_security
from flask_security.confirmable import confirm_email_token_status, \
    generate_confirmation_token
from flask_security.recoverable import generate_reset_password_token


def test_forgot_password_token(app):
    """Test expiration of token for password reset."""
    ds = app.extensions['invenio-accounts'].datastore
    user = ds.create_user(email='test@test.ch', password='testch', active=True)
    ds.commit()
    token = generate_reset_password_token(user)
    reset_link = url_for_security('reset_password', token=token)

    with app.test_client() as client:
        res = client.get(reset_link, follow_redirects=True)
        reset_btn = (
            '<button type="submit" class="btn btn-primary btn-lg '
            'btn-block">Reset Password</button>'
        )
        assert reset_btn in res.get_data()
        time.sleep(4)
        res = client.get(reset_link, follow_redirects=True)
        msg = app.config['SECURITY_MSG_PASSWORD_RESET_EXPIRED'][0] % {
            'within': app.config['SECURITY_RESET_PASSWORD_WITHIN'],
            'email': user.email
        }
        assert msg in res.get_data()


def test_confirmation_token(app):
    """Test expiration of token for email confirmation."""
    ds = app.extensions['invenio-accounts'].datastore
    user = ds.create_user(email='test@test.ch', password='testch', active=True)
    ds.commit()
    token = generate_confirmation_token(user)
    expired, invalid, token_user = confirm_email_token_status(token)
    assert expired is False and invalid is False and token_user is user
    time.sleep(4)
    expired, invalid, token_user = confirm_email_token_status(token)
    assert expired is True and invalid is False and token_user is user
