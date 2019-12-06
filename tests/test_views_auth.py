# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2019 CERN.
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


"""Test authentication REST API views."""

from __future__ import absolute_import, print_function

import json

import pytest
from flask import url_for
from invenio_accounts.models import User
from invenio_db import db


def assert_error_fields(res, expected):
    errors = res.json['errors']
    for field, msg in expected:
        assert any(
            e['field'] == field and msg in e['message'].lower()
            for e in errors), errors


def test_login_view(api):
    app = api

    with app.app_context():
        with app.test_client() as client:
            url = url_for('invenio_accounts_rest_auth.login')
            # Missing fields
            res = client.post(url)
            assert res.status_code == 400
            assert_error_fields(res, (
                ('password', 'required'),
                ('email', 'required'),
            ))

            # Invalid fields
            res = client.post(
                url, json={'email': 'invalid-email', 'password': 'short'})
            assert res.status_code == 400
            assert_error_fields(res, (
                ('password', 'length'),
                ('email', 'not a valid email'),
                ('email', 'user does not exist'),  # TODO: do we want this?
            ))

            # Invalid credentials
            res = client.post(
                url, json={'email': 'not@exists.com', 'password': '123456'})
            assert res.status_code == 400
            assert_error_fields(res, (
                ('email', 'user does not exist'),
            ))
