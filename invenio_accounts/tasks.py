# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Background tasks for accounts."""

from datetime import datetime

from celery import shared_task
from flask import current_app
from flask_mail import Message
from invenio_db import db

from .models import LoginInformation, SessionActivity
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

    To enable a periodically clean of the session table, you should configure
    the task as a celery periodic task.

    .. code-block:: python

        from datetime import timedelta
        CELERYBEAT_SCHEDULE = {
            'session_cleaner': {
                'task': 'invenio_accounts.tasks.clean_session_table',
                'schedule': timedelta(days=1),
            },
        }

    See `Invenio-Celery <https://invenio-celery.readthedocs.io/>`_
    documentation for further details.
    """
    sessions = SessionActivity.query_by_expired().all()
    for session in sessions:
        delete_session(sid_s=session.sid_s)
    db.session.commit()


@shared_task
def delete_ips():
    """Automatically remove login_info.last_login_ip older than 30 days."""
    expiration_date = datetime.utcnow() - \
        current_app.config['ACCOUNTS_RETENTION_PERIOD']

    LoginInformation.query.filter(
        LoginInformation.last_login_ip.isnot(None),
        LoginInformation.last_login_at < expiration_date
    ).update({
        LoginInformation.last_login_ip: None
    })

    LoginInformation.query.filter(
        LoginInformation.current_login_ip.isnot(None),
        LoginInformation.current_login_at < expiration_date
    ).update({
        LoginInformation.current_login_ip: None
    })
    db.session.commit()
