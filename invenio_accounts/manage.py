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

from sys import stderr

from invenio.ext.script import Manager
from invenio.ext.sqlalchemy import db

from sqlalchemy.orm.exc import NoResultFound

from .helpers import send_account_activation_email
from .models import User
from .validators import validate_email, validate_email_is_available,\
    validate_nickname, validate_nickname_is_available, validate_password

manager = Manager(usage=__doc__)


__failed_to_delete_account = 'failed to delete the account:'
__failed_to_activate_account = 'failed to activate the account:'
__failed_to_deactivate_account = 'failed to deactivate the account:'
__failed_to_set_password = 'failed to set the password:'
__no_user_with_email = 'no user was found with email {0}'


@manager.command
@manager.option('--nickname', '-n', dest='nickname')
@manager.option('--email', '-e', dest='email')
@manager.option('--password', '-p', dest='password')
@manager.option('--activate', '-p', dest='activate', action='store_true')
def create(nickname, email, password, activate=False):
    """Create a new account."""
    try:
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

        db.session.begin(subtransactions=True)
        db.session.add(user)
        db.session.commit()
        db.session.commit()

        print(('succesfully created account {0} with nickname {1}')
              .format(email, nickname))
        if activate:
            print('account has been activated')
        else:
            send_account_activation_email(user)
            print('activation email has been sent')
    except Exception as e:
        db.session.rollback()
        print('failed to create a new account:', e, file=stderr)
        exit(1)


@manager.command
@manager.option('--email', '-e', dest='email')
def delete(email):
    """Delete an account."""
    try:
        db.session.begin(subtransactions=True)
        user = User.get_by_email(email)
        db.session.delete(user)
        db.session.commit()
        db.session.commit()
        print('successfully deleted account', email)
    except NoResultFound as e:
        db.session.rollback()
        print(__failed_to_delete_account,
              __no_user_with_email.format(email), file=stderr)
        exit(1)
    except Exception as e:
        db.session.rollback()
        print(__failed_to_delete_account, e, file=stderr)
        exit(1)


@manager.command
@manager.option('--email', '-e', dest='email')
def activate(email):
    """Activate an account."""
    try:
        db.session.begin(subtransactions=True)
        user = User.get_by_email(email)
        user.activate()
        db.session.commit()
        db.session.commit()
        print('succesfully activated the account', email)
    except NoResultFound as e:
        db.session.rollback()
        print(__failed_to_activate_account,
              __no_user_with_email.format(email), file=stderr)
        exit(1)
    except Exception as e:
        db.session.rollback()
        print(__failed_to_activate_account, e, file=stderr)
        exit(1)


@manager.command
@manager.option('--email', '-e', dest='email')
def deactivate(email):
    """Deactivate an account."""
    try:
        db.session.begin(subtransactions=True)
        user = User.get_by_email(email)
        user.deactivate()
        db.session.commit()
        db.session.commit()
        print('successfully deactivated the account', email)
    except NoResultFound as e:
        db.session.rollback()
        print(__failed_to_deactivate_account,
              __no_user_with_email.format(email), file=stderr)
        exit(1)
    except Exception as e:
        db.session.rollback()
        print(__failed_to_deactivate_account, e, file=stderr)
        exit(1)


@manager.command
@manager.option('--email', '-e', dest='email')
@manager.option('--password', '-p', dest='password')
def password(email, password):
    """Set a password for an account."""
    try:
        db.session.begin(subtransactions=True)
        validate_password(password)
        user = User.get_by_email(email)
        user.password = password
        db.session.commit()
        db.session.commit()
        print("password successfully set for", email)
    except NoResultFound as e:
        db.session.rollback()
        print(__failed_to_set_password,
              __no_user_with_email.format(email), file=stderr)
        exit(1)
    except Exception as e:
        db.session.rollback()
        print(__failed_to_set_password, e, file=stderr)
        exit(1)


def main():
    """Run manager."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()
