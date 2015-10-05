# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Perform account operations."""

from __future__ import print_function

from invenio_ext.script import Manager
from invenio_ext.sqlalchemy import db

from .helpers import send_account_activation_email
from .models import User
from .validators import validate_email, validate_email_is_available,\
    validate_nickname, validate_nickname_is_available, validate_password

manager = Manager(usage=__doc__)


@manager.command
@manager.option('nickname', dest='nickname')
@manager.option('email', dest='email')
@manager.option('password', dest='password')
@manager.option('--activate', '-a', dest='activate', action='store_true')
def create(nickname, email, password, activate=False):
    """Create a new account."""
    validate_nickname(nickname)
    validate_nickname_is_available(nickname)
    validate_email(email)
    validate_email_is_available(email)
    validate_password(password)

    user = User()
    user.nickname = nickname
    user.email = email
    user.password = password
    if activate:
        user.activate()
    else:
        user.unverify_email()

    with db.session.begin_nested():
        db.session.add(user)
    db.session.commit()

    print(('succesfully created account {0} with nickname {1}')
          .format(email, nickname))
    if activate:
        print('account has been activated')
    else:
        send_account_activation_email(user)
        print('activation email has been sent')


@manager.command
@manager.option('email', dest='email')
def delete(email):
    """Delete an account."""
    with db.session.begin_nested():
        User.query.filter_by(email=email).delete()
    db.session.commit()
    print('successfully deleted account', email)


@manager.command
@manager.option('email', dest='email')
def activate(email):
    """Activate an account."""
    with db.session.begin_nested():
        User.update().where(User.email == email).values(note="1")
    db.session.commit()
    print('succesfully activated the account', email)


@manager.command
@manager.option('email', dest='email')
def deactivate(email):
    """Deactivate an account."""
    with db.session.begin_nested():
        User.update().where(User.email == email).values(note="0")
    db.session.commit()
    print('successfully deactivated the account', email)


@manager.command
@manager.option('email', dest='email')
@manager.option('password', dest='password')
def password(email, password):
    """Set a password for an account."""
    validate_password(password)
    with db.session.begin_nested():
        user = User.query.filter_by(email=email).one()
        user.password = password
    db.session.commit()
    print("password successfully set for", email)


def main():
    """Run manager."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()
