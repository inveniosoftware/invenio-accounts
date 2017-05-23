# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
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

"""Utility function for ACCOUNTS."""

import uuid
from datetime import datetime

from flask import current_app
from flask_login import current_user
from future.utils import raise_from
from jwt import DecodeError, ExpiredSignatureError, decode, encode

from .errors import JWTDecodeError, JWTExpiredToken


def jwt_create_token(user_id=None, additional_data=None):
    """Encode the JWT token.

    :param int user_id: Addition of user_id.
    :param dict additional_data: Additional information for the token.
    :returns: The encoded token.
    :rtype: str

    .. note::
        Definition of the JWT claims:

        * exp: ((Expiration Time) expiration time of the JWT.
        * sub: (subject) the principal that is the subject of the JWT.
        * jti: (JWT ID) UID for the JWT.
    """
    # Create an ID
    uid = str(uuid.uuid4())
    # The time in UTC now
    now = datetime.utcnow()
    # Build the token data
    token_data = {
        'exp': now + current_app.config['ACCOUNTS_JWT_EXPIRATION_DELTA'],
        'sub': user_id or current_user.get_id(),
        'jti': uid,
    }
    # Add any additional data to the token
    if additional_data is not None:
        token_data.update(additional_data)

    # Encode the token and send it back
    encoded_token = encode(
        token_data,
        current_app.config['ACCOUNTS_JWT_SECRET_KEY'],
        current_app.config['ACCOUNTS_JWT_ALOGORITHM']
    ).decode('utf-8')
    return encoded_token


def jwt_decode_token(token):
    """Decode the JWT token.

    :param str token: Additional information for the token.
    :returns: The token data.
    :rtype: dict
    """
    try:
        return decode(
            token,
            current_app.config['ACCOUNTS_JWT_SECRET_KEY'],
            algorithms=[
                current_app.config['ACCOUNTS_JWT_ALOGORITHM']
            ]
        )
    except DecodeError as exc:
        raise_from(JWTDecodeError(), exc)
    except ExpiredSignatureError as exc:
        raise_from(JWTExpiredToken(), exc)
