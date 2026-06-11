# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
# Copyright (C) 2024-2025 Graz University of Technology.
# Copyright (C) 2026 KTH Royal Institute of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Module tests."""

from datetime import datetime, timedelta, timezone
from time import sleep
from unittest import mock

import pytest
from flask import url_for
from flask_login import login_required
from flask_mail import Message
from flask_security import url_for_security
from invenio_db import db

from invenio_accounts.models import SessionActivity, User
from invenio_accounts.proxies import current_datastore, current_db_change_history
from invenio_accounts.tasks import clean_session_table, delete_ips, send_security_email
from invenio_accounts.testutils import create_test_user


def test_send_message_outbox(task_app):
    """Test sending a security message using Task module."""
    with task_app.app_context():
        with task_app.extensions["mail"].record_messages() as outbox:
            msg = Message(
                "Test1", sender="test1@test1.test1", recipients=["test1@test1.test1"]
            )

            send_security_email(msg.__dict__)

            assert len(outbox) == 1
            sent_msg = outbox[0]
            assert sent_msg.subject == "Test1"
            assert sent_msg.sender == "test1@test1.test1"
            assert sent_msg.recipients == ["test1@test1.test1"]


def test_send_message_through_security(task_app):
    """Test sending a message through security extension."""
    with task_app.app_context():
        with task_app.extensions["mail"].record_messages() as outbox:
            msg = Message(
                "Test1", sender="test1@test1.test1", recipients=["test1@test1.test1"]
            )

            task_app.extensions["security"]._send_mail_task(msg)

            assert len(outbox) == 1
            sent_msg = outbox[0]
            assert sent_msg.subject == "Test1"
            assert sent_msg.sender == "test1@test1.test1"
            assert sent_msg.recipients == ["test1@test1.test1"]


def test_clean_session_table(task_app):
    """Test clean session table."""
    # set session lifetime
    task_app.permanent_session_lifetime = timedelta(seconds=20)

    # protected page
    @task_app.route("/test", methods=["GET"])
    @login_required
    def test():
        return "test"

    with task_app.test_request_context():
        user1 = create_test_user(email="user1@invenio-software.org")
        user2 = create_test_user(email="user2@invenio-software.org")

        with task_app.test_client() as client:
            client.post(
                url_for_security("login"),
                data=dict(
                    email=user1.email,
                    password=user1.password_plaintext,
                ),
            )
        assert len(db.session.query(SessionActivity).all()) == 1
        sleep(15)

        with task_app.test_client() as client:
            client.post(
                url_for_security("login"),
                data=dict(
                    email=user2.email,
                    password=user2.password_plaintext,
                ),
            )
            assert len(db.session.query(SessionActivity).all()) == 2
            sleep(10)

            clean_session_table.s().apply()
            assert len(db.session.query(SessionActivity).all()) == 1

            protected_url = url_for("test")

            res = client.get(protected_url)
            assert res.status_code == 200

            sleep(15)
            clean_session_table.s().apply()
            assert len(db.session.query(SessionActivity).all()) == 0

            res = client.get(protected_url)
            # check if the user is really logout
            assert res.status_code == 302


def test_delete_ips(task_app, monkeypatch):
    """Test if ips are deleted after 30 days."""
    last_login_at1 = (
        datetime.now(timezone.utc)
        - task_app.config["ACCOUNTS_RETENTION_PERIOD"]
        - timedelta(days=1)
    )
    last_login_at2 = datetime.now(timezone.utc)

    with task_app.app_context():
        task_app.config["ACCOUNTS_IP_CLEANUP_BATCH_SIZE"] = 1
        user1 = create_test_user(
            email="user1@invenio-software.org",
            last_login_ip="127.0.0.1",
            current_login_ip="127.0.0.1",
            last_login_at=last_login_at1,
            current_login_at=last_login_at1,
        )

        user2 = create_test_user(
            email="user2@invenio-software.org",
            last_login_ip="127.0.0.1",
            current_login_ip="127.0.0.1",
            last_login_at=last_login_at2,
            current_login_at=last_login_at2,
        )

        user3 = create_test_user(
            email="user3@invenio-software.org",
            last_login_ip="127.0.0.1",
            current_login_ip="127.0.0.1",
            last_login_at=last_login_at1,
            current_login_at=last_login_at2,
        )
        user_versions = {
            user1.id: user1.version_id,
            user2.id: user2.version_id,
            user3.id: user3.version_id,
        }

        datastore = current_datastore._get_current_object()
        marked_user_ids = []
        original_mark_changed = datastore.mark_changed

        def mark_changed(sid, uid=None, rid=None, model=None):
            marked_user_ids.append(uid)
            return original_mark_changed(sid, uid=uid, rid=rid, model=model)

        monkeypatch.setattr(datastore, "mark_changed", mark_changed)

        delete_ips()

        user = db.session.query(User).filter(User.id == user1.id).one()
        assert user.last_login_ip is None
        assert user.current_login_ip is None
        assert user.version_id == user_versions[user1.id] + 1

        user = db.session.query(User).filter(User.id == user2.id).one()
        assert user.last_login_ip is not None
        assert user.current_login_ip is not None
        assert user.version_id == user_versions[user2.id]

        user = db.session.query(User).filter(User.id == user3.id).one()
        assert user.last_login_ip is None
        assert user.current_login_ip is not None
        assert user.version_id == user_versions[user3.id] + 1

        assert sorted(marked_user_ids) == sorted([user1.id, user3.id])


def test_delete_ips_rolls_back_failed_batch(task_app):
    """Test that IP cleanup rolls back when a batch fails before commit."""
    last_login_at = (
        datetime.now(timezone.utc)
        - task_app.config["ACCOUNTS_RETENTION_PERIOD"]
        - timedelta(days=1)
    )

    with task_app.app_context():
        user = create_test_user(
            email="rollback@invenio-software.org",
            last_login_ip="127.0.0.1",
            current_login_ip="127.0.0.1",
            last_login_at=last_login_at,
            current_login_at=last_login_at,
        )
        user_version = user.version_id
        datastore = current_datastore._get_current_object()

        with mock.patch.object(
            datastore, "mark_changed", side_effect=RuntimeError("failed")
        ):
            with pytest.raises(RuntimeError):
                delete_ips()

        db.session.expire_all()
        user = db.session.query(User).filter(User.id == user.id).one()
        assert user.last_login_ip is not None
        assert user.current_login_ip is not None
        assert user.version_id == user_version
        assert id(db.session) not in current_db_change_history.sessions
