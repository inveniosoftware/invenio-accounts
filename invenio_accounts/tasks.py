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

"""Background tasks for accounts."""

from __future__ import absolute_import, print_function

from celery import shared_task
from flask import current_app
from flask_mail import Message
from invenio_db import db

from .models import SessionActivity
from .proxies import current_accounts
from .sessions import delete_session


@shared_task
def send_security_email(data):
    """Celery task to send security email.

    :param data: Contains the email data.
    """
    msg = Message()
    msg.__dict__.update(data)
    current_app.extensions['mail'].send(msg)


@shared_task
def clean_session_table():
    """Automatically clean session table.

    To enable a periodically clean, you should configure the task as a
    celery periodic task.

    .. code-block:: python

        from datetime import timedelta
        CELERYBEAT_SCHEDULE = {
            'session_cleaner': {
                'task': 'invenio_accounts.tasks.clean_session_table',
                'schedule': timedelta(days=1),
            },
        }

    See ``invenio-celery`` documentation to have more details.
    """
    sessions = SessionActivity.query_by_expired().all()
    for session in sessions:
        delete_session(sid_s=session.sid_s)
    db.session.commit()
