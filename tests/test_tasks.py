# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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


"""Module tests."""

from __future__ import absolute_import, print_function

from datetime import timedelta
from time import sleep

from flask import url_for
from flask_login import login_required
from flask_mail import Message
from flask_security import url_for_security

from invenio_accounts.models import SessionActivity
from invenio_accounts.tasks import clean_session_table, send_security_email
from invenio_accounts.testutils import create_test_user


def test_send_message_outbox(task_app):
    """Test sending a security message using Task module."""
    with task_app.app_context():
        with task_app.extensions['mail'].record_messages() as outbox:
            msg = Message('Test1',
                          sender='test1@test1.test1',
                          recipients=['test1@test1.test1'])

            send_security_email(msg.__dict__)

            assert len(outbox) == 1
            sent_msg = outbox[0]
            assert sent_msg.subject == 'Test1'
            assert sent_msg.sender == 'test1@test1.test1'
            assert sent_msg.recipients == ['test1@test1.test1']


def test_send_message_through_security(task_app):
    """Test sending a message through security extension."""
    with task_app.app_context():
        with task_app.extensions['mail'].record_messages() as outbox:
            msg = Message('Test1',
                          sender='test1@test1.test1',
                          recipients=['test1@test1.test1'])

            task_app.extensions['security']._send_mail_task(msg)

            assert len(outbox) == 1
            sent_msg = outbox[0]
            assert sent_msg.subject == 'Test1'
            assert sent_msg.sender == 'test1@test1.test1'
            assert sent_msg.recipients == ['test1@test1.test1']


def test_clean_session_table(task_app):
    """Test clean session table."""
    # set session lifetime
    task_app.permanent_session_lifetime = timedelta(seconds=20)
    with task_app.test_request_context():
        user1 = create_test_user(email='user1@invenio-software.org')
        user2 = create_test_user(email='user2@invenio-software.org')

        with task_app.test_client() as client:
            client.post(url_for_security('login'), data=dict(
                email=user1.email,
                password=user1.password_plaintext,
            ))
        assert len(SessionActivity.query.all()) == 1
        sleep(15)

        with task_app.test_client() as client:
            # protected page
            @task_app.route('/test', methods=['GET'])
            @login_required
            def test():
                return 'test'

            client.post(url_for_security('login'), data=dict(
                email=user2.email,
                password=user2.password_plaintext,
            ))
            assert len(SessionActivity.query.all()) == 2
            sleep(10)

            clean_session_table.s().apply()
            assert len(SessionActivity.query.all()) == 1

            protected_url = url_for('test')

            res = client.get(protected_url)
            assert res.status_code == 200

            sleep(15)
            clean_session_table.s().apply()
            assert len(SessionActivity.query.all()) == 0

            res = client.get(protected_url)
            # check if the user is really logout
            assert res.status_code == 302
