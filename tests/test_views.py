# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
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

"""Test account views."""

from flask_babelex import gettext as _
from flask_security import url_for_security

from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint


def test_no_log_in_message_for_logged_in_users(app):
    """Test the password reset form for logged in users.

    Password reset form should not show log in or sign up messages for logged
    in users.
    """
    with app.app_context():
        forgot_password_url = url_for_security('forgot_password')

    with app.test_client() as client:
        log_in_message = _('Log In').encode('utf-8')
        sign_up_message = _('Sign Up').encode('utf-8')

        resp = client.get(forgot_password_url)
        assert resp.status_code == 200
        assert log_in_message in resp.data
        assert sign_up_message in resp.data

        test_email = 'info@inveniosoftware.org'
        test_password = 'test1234'
        resp = client.post(url_for_security('register'), data=dict(
            email=test_email,
            password=test_password,
        ), environ_base={'REMOTE_ADDR': '127.0.0.1'})

        resp = client.post(url_for_security('login'), data=dict(
            email=test_email,
            password=test_password,
        ))

        resp = client.get(forgot_password_url, follow_redirects=True)
        if resp.status_code == 200:
            # This behavior will be phased out in future Flask-Security
            # release as per mattupstate/flask-security#291
            assert log_in_message not in resp.data
            assert sign_up_message not in resp.data
        else:
            # Future Flask-Security will redirect to post login view when
            # authenticated user requests password reset page.
            assert resp.data == client.get(
                app.config['SECURITY_POST_LOGIN_VIEW']).data
