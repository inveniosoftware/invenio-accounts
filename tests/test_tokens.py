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
# -*- coding: utf-8 -*-
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""Token creation and validation test case."""

from __future__ import absolute_import

from itsdangerous import SignatureExpired

from invenio_testing import InvenioTestCase

from invenio_accounts.tokens import EmailConfirmationSerializer


class EmailConfirmationSerializerTestCase(InvenioTestCase):

    """Test case for email link token."""

    extra_data = dict(email="info@invenio-software.org")

    def test_create_validate(self):
        """Test token creation."""
        s = EmailConfirmationSerializer()
        t = s.create_token(1, self.extra_data)
        data = s.validate_token(t, expected_data=self.extra_data)
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['data'], dict(email="info@invenio-software.org"))

    def test_expired(self):
        """Test token expiry."""
        s = EmailConfirmationSerializer(expires_in=-20)
        t = s.create_token(1, self.extra_data)
        self.assertIsNone(s.validate_token(t))
        self.assertIsNone(s.validate_token(t, expected_data=self.extra_data))
        self.assertRaises(SignatureExpired, s.load_token, t)
        self.assertIsNotNone(s.load_token(t, force=True))

    def test_expected_data_mismatch(self):
        """Test token validation."""
        s = EmailConfirmationSerializer()
        t = s.create_token(1, self.extra_data)
        self.assertIsNotNone(s.validate_token(t))
        self.assertIsNone(s.validate_token(t, dict(notvalid=1)))
        self.assertIsNone(s.validate_token(t, dict(email='another@email')))

    def test_creation(self):
        """Ensure that no two tokens are identical."""
        s = EmailConfirmationSerializer()
        t1 = s.create_token(1, self.extra_data)
        t2 = s.create_token(1, self.extra_data)
        self.assertNotEqual(t1, t2)
