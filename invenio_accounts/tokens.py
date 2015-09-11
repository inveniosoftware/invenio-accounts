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
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""Token serializers."""

import binascii
import os

from base64 import urlsafe_b64encode
from datetime import datetime

from itsdangerous import BadData, JSONWebSignatureSerializer, \
    SignatureExpired, TimedJSONWebSignatureSerializer

from invenio_base.globals import cfg


class TokenMixin(object):

    """Mix-in class for token serializers."""

    def create_token(self, obj_id, extra_data):
        """Create a token referencing the object id with extra data.

        Note random data is added to ensure that no two tokens are identical.
        """
        return self.dumps(dict(id=obj_id, data=extra_data,
                               rnd=binascii.hexlify(os.urandom(4))))

    def validate_token(self, token, expected_data=None):
        """Validate secret link token.

        :param token: Token value.
        :param expected_data: A dictionary of key/values that must be present
            in the data part of the token (i.e. included via ``extra_data`` in
            ``create_token``).
        """
        try:
            # Load token and remove random data.
            data = self.load_token(token)

            # Compare expected data with data in token.
            if expected_data:
                for k in expected_data:
                    if expected_data[k] != data["data"].get(k):
                        return None
            return data
        except BadData:
            return None

    def load_token(self, token, force=False):
        """Load data in a token.

        :param token: Token to load.
        :param force: Load token data even if signature expired.
                      Default: False.
        """
        try:
            data = self.loads(token)
        except SignatureExpired as e:
            if not force:
                raise
            data = e.payload

        del data["rnd"]
        return data


class EmailConfirmationSerializer(TimedJSONWebSignatureSerializer, TokenMixin):

    """Serializer for email confirmation link tokens.

    Depends upon the secrecy of ``SECRET_KEY``. Tokens expire after a specific
    time (defaults to ``ACCOUNTS_CONFIRMLINK_EXPIRES_IN``). The
    access request id as well as the email address is stored in the token
    together with a random bit to ensure all tokens are unique.
    """

    def __init__(self, expires_in=None):
        """Initialize underlying TimedJSONWebSignatureSerializer."""
        dt = expires_in or cfg.get('ACCOUNTS_CONFIRMLINK_EXPIRES_IN')

        super(EmailConfirmationSerializer, self).__init__(
            cfg['SECRET_KEY'],
            expires_in=dt,
            salt='accounts-email',
        )
