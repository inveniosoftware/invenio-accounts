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

import pytest
from flask import current_app, url_for
from flask.ext.security.utils import encrypt_password
from flask_admin import Admin, menu
from invenio_admin import InvenioAdmin
from invenio_db import db
from werkzeug.local import LocalProxy

from invenio_accounts import InvenioAccounts
from invenio_accounts.admin import role_adminview, user_adminview
from invenio_accounts.cli import users_create

_datastore = LocalProxy(
    lambda: current_app.extensions['security'].datastore
)


def test_admin(app):
    """Test flask-admin interace."""
    assert isinstance(role_adminview, dict)
    assert isinstance(user_adminview, dict)

    assert 'model' in role_adminview
    assert 'modelview' in role_adminview
    assert 'model' in user_adminview
    assert 'modelview' in user_adminview

    admin = Admin(app, name="Test")

    user_model = user_adminview.pop('model')
    user_view = user_adminview.pop('modelview')
    admin.add_view(user_view(user_model, db.session, **user_adminview))

    # Test activation and deactivation

    with app.app_context():
        # create user and save url for testing
        request_url = url_for("user.action_view")
        kwargs = dict(email="test@test.cern", active=False,
                      password=encrypt_password('aafaf4as5fa'))
        _datastore.create_user(**kwargs)
        _datastore.commit()
        inserted_id = _datastore.get_user('test@test.cern').id

    with app.test_client() as client:

        res = client.post(
            request_url,
            data={'rowid': inserted_id, 'action': 'activate'},
            follow_redirects=True
        )
        assert res.status_code == 200

        res = client.post(
            request_url,
            data={'rowid': inserted_id, 'action': 'inactivate'},
            follow_redirects=True
        )
        assert res.status_code == 200

        pytest.raises(
            ValueError, client.post, request_url,
            data={'rowid': -42, 'action': 'inactivate'},
            follow_redirects=True
        )
        pytest.raises(
            ValueError, client.post, request_url,
            data={'rowid': -42, 'action': 'activate'},
            follow_redirects=True
        )
