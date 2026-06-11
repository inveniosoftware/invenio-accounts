# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2025 CERN.
# Copyright (C) 2024-2025 Graz University of Technology.
# Copyright (C) 2026 KTH Royal Institute of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Background tasks for accounts."""

from datetime import datetime, timezone

from celery import shared_task
from flask import current_app
from flask_mail import Message
from invenio_db import db
from sqlalchemy import and_, func, or_

from .models import Domain, LoginInformation, SessionActivity, User
from .proxies import current_datastore, current_db_change_history
from .sessions import delete_session


@shared_task
def send_security_email(data):
    """Celery task to send security email.

    :param data: Contains the email data.
    """
    msg = Message()
    msg.__dict__.update(data)
    current_app.extensions["mail"].send(msg)


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
    expired_sids = [s.sid_s for s in SessionActivity.query_by_expired()]
    for sid_s in expired_sids:
        try:
            delete_session(sid_s=sid_s)
        except Exception as e:
            current_app.logger.warning(f"Failed to delete session {sid_s}: {e}")
    db.session.commit()


@shared_task
def delete_ips():
    """Remove expired login IPs and mark affected users for reindexing."""
    now = datetime.now(timezone.utc)
    expiration_date = now - current_app.config["ACCOUNTS_RETENTION_PERIOD"]
    batch_size = current_app.config["ACCOUNTS_IP_CLEANUP_BATCH_SIZE"]
    expired_last_login_ip = and_(
        LoginInformation.last_login_ip.isnot(None),
        LoginInformation.last_login_at < expiration_date,
    )
    expired_current_login_ip = and_(
        LoginInformation.current_login_ip.isnot(None),
        LoginInformation.current_login_at < expiration_date,
    )

    while True:
        affected_user_ids = [
            row.user_id
            for row in db.session.query(LoginInformation.user_id)
            .filter(or_(expired_last_login_ip, expired_current_login_ip))
            .order_by(LoginInformation.user_id)
            .distinct()
            .limit(batch_size)
        ]
        if not affected_user_ids:
            return

        try:
            db.session.query(LoginInformation).filter(
                LoginInformation.user_id.in_(affected_user_ids), expired_last_login_ip
            ).update({LoginInformation.last_login_ip: None}, synchronize_session=False)

            db.session.query(LoginInformation).filter(
                LoginInformation.user_id.in_(affected_user_ids),
                expired_current_login_ip,
            ).update(
                {LoginInformation.current_login_ip: None}, synchronize_session=False
            )

            db.session.query(User).filter(User.id.in_(affected_user_ids)).update(
                {
                    User.updated: db.func.now(),
                    # User indexing uses version_id as the record revision, so
                    # bulk changes must advance it to replace the search doc.
                    User.version_id: User.version_id + 1,
                },
                synchronize_session=False,
            )

            # Bulk updates bypass ORM dirty tracking; mark IDs for post-commit reindex.
            for user_id in affected_user_ids:
                current_datastore.mark_changed(id(db.session), uid=user_id)

            # Commit per batch to bound transactions and reindex task payloads.
            current_datastore.commit()
            current_app.logger.info(
                "delete_ips task: cleared IPs for %d users", len(affected_user_ids)
            )
        except Exception:
            db.session.rollback()
            current_db_change_history.clear_dirty_sets(db.session)
            raise


@shared_task
def update_domain_status():
    """Update domain statistics."""
    # This subquery calculate the number of users per domain from the users
    # table.
    subquery = (
        db.session.query(
            User.domain,
            func.count(User.id).label("num_users"),
            func.count(User.active).filter(User.active == True).label("num_active"),
            func.count(User.active).filter(User.active == False).label("num_inactive"),
            func.count(User.confirmed_at).label("num_confirmed"),
            func.count(User.verified_at).label("num_verified"),
            func.count(User.blocked_at).label("num_blocked"),
        )
        .group_by(User.domain)
        .subquery("n")
    )

    # Using above subquery, we find the domains that has changed.
    stmt = (
        db.session.query(
            Domain.domain,
            subquery.c.num_users,
            subquery.c.num_active,
            subquery.c.num_inactive,
            subquery.c.num_confirmed,
            subquery.c.num_verified,
            subquery.c.num_blocked,
        )
        .join(subquery, Domain.domain == subquery.c.domain)
        .filter(
            or_(
                Domain.num_users != subquery.c.num_users,
                Domain.num_active != subquery.c.num_active,
                Domain.num_inactive != subquery.c.num_inactive,
                Domain.num_confirmed != subquery.c.num_confirmed,
                Domain.num_verified != subquery.c.num_verified,
                Domain.num_blocked != subquery.c.num_blocked,
            )
        )
    )

    # If statistics are updated regularly, the number of updates is relatively
    # low and hence fit in memory. We read all data first, to avoid starting
    # to modify the same table we're reading from.
    domain_updates = list(stmt.all())

    # Commit batches of 500 updates
    batch_size = 500
    now = datetime.now(timezone.utc)

    # Process updates in batches
    for i in range(0, len(domain_updates), batch_size):
        with db.session.begin_nested():  # Use nested transactions for safety
            for (
                domain,
                users,
                active,
                inactive,
                confirmed,
                verified,
                blocked,
            ) in domain_updates[i : i + batch_size]:
                db.session.query(Domain).filter(Domain.domain == domain).update(
                    {
                        "num_users": users,
                        "num_active": active,
                        "num_inactive": inactive,
                        "num_confirmed": confirmed,
                        "num_verified": verified,
                        "num_blocked": blocked,
                        "updated": now,
                    }
                )
        db.session.commit()  # Commit after each batch
