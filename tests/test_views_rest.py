# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE

"""Test authentication REST API views."""

from __future__ import absolute_import, print_function

import json

from flask import url_for
from invenio_db import db

from invenio_accounts.testutils import create_test_user


def get_json(response):
    """Get JSON from response."""
    return json.loads(response.get_data(as_text=True))


def assert_error_resp(res, expected_errors, expected_status_code=400):
    """Assert errors in a client response."""
    assert res.status_code == expected_status_code
    payload = get_json(res)
    errors = payload.get('errors', [])
    for field, msg in expected_errors:
        if not field:  # top-level "message" error
            assert msg in payload['message'].lower()
            continue
        assert any(
            e['field'] == field and msg in e['message'].lower()
            for e in errors), payload


def test_login_view(api):
    app = api
    with app.app_context():

        normal_user = create_test_user(email='normal@test.com')
        create_test_user(email='disabled@test.com', active=False)
        create_test_user(email='nopass@test.com', password=None)

        db.session.commit()

        with app.test_client() as client:
            url = url_for('invenio_accounts_rest_auth.login')
            # Missing fields
            res = client.post(url)
            assert_error_resp(res, (
                ('password', 'required'),
                ('email', 'required'),
            ))

            # Invalid fields
            res = client.post(url, data=dict(
                email='invalid-email', password='short'))
            assert_error_resp(res, (
                ('password', 'length'),
                ('email', 'not a valid email'),
            ))

            # Invalid credentials
            res = client.post(url, data=dict(
                email='not@exists.com', password='123456'))
            assert_error_resp(res, (
                ('email', 'user does not exist'),
            ))

            # No-password user
            res = client.post(url, data=dict(
                email='nopass@test.com', password='123456'))
            assert_error_resp(res, (
                ('password', 'no password is set'),
            ))

            # Disabled account
            res = client.post(url, data=dict(
                email='disabled@test.com', password='123456'))
            assert_error_resp(res, (
                (None, 'account is disabled'),
            ))

            # Successful login
            res = client.post(url, data=dict(
                email='normal@test.com', password='123456'))
            payload = get_json(res)
            assert res.status_code == 200
            assert payload['id'] == normal_user.id
            assert payload['email'] == normal_user.email
            session_cookie = next(
                c for c in client.cookie_jar if c.name == 'session')
            assert session_cookie is not None
            assert session_cookie.value

            # User info view
            res = client.get(url_for('invenio_accounts_rest_auth.user_info'))
            payload = get_json(res)
            assert res.status_code == 200
            assert payload['id'] == normal_user.id


def test_registration_view(api):
    app = api
    with app.app_context():
        create_test_user(email='old@test.com')
        db.session.commit()
        with app.test_client() as client:
            url = url_for('invenio_accounts_rest_auth.register')

            # Missing fields
            res = client.post(url)
            assert_error_resp(res, (
                ('password', 'required'),
                ('email', 'required'),
            ))

            # Invalid fields
            res = client.post(url, data=dict(
                email='invalid-email', password='short'))
            assert_error_resp(res, (
                ('password', 'length'),
                ('email', 'not a valid email'),
            ))

            # Existing user
            res = client.post(url, data=dict(
                email='old@test.com', password='123456'))
            assert_error_resp(res, (
                ('email', 'old@test.com is already associated'),
            ))

            # Successful registration
            res = client.post(url, data=dict(
                email='new@test.com', password='123456'))
            payload = get_json(res)
            assert res.status_code == 200
            assert payload['id'] == 2
            assert payload['email'] == 'new@test.com'
            session_cookie = next(
                c for c in client.cookie_jar if c.name == 'session')
            assert session_cookie is not None
            assert session_cookie.value

            res = client.get(url_for('invenio_accounts_rest_auth.user_info'))
            assert res.status_code == 200
