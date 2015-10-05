# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2010, 2011, 2013, 2015 CERN.
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

"""Unit tests for the user handling library."""

from mock import patch

from invenio_testing import InvenioTestCase


class UserTestCase(InvenioTestCase):

    """Test User class."""

    @property
    def config(self):
        """Config."""
        cfg = super(UserTestCase, self).config
        cfg['PACKAGES'] = [
            'invenio_base',
            'invenio_accounts',
        ]
        return cfg

    def test_note_is_converted_to_string(self):
        from invenio_accounts.models import User
        u = User(email="test@test.pl", password="")
        u.note = 2
        self.assertTrue(isinstance(u.note, str))

    @patch('invenio_accounts.utils.send_email')
    def test_verify_email_works_with_numbers_and_strings(self, send_email):
        from invenio_accounts.models import User
        u = User(email="test@test.pl", password="")
        u.note = 2
        self.assertTrue(u.verify_email())

        u2 = User(email="test2@test2.pl", password="")
        u2.note = "2"

        send_email.return_value = True

        self.assertTrue(u2.verify_email())
