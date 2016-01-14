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

from flask_mail import Message

from invenio_accounts.tasks import send_security_email


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
