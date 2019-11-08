# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Utility function for ACCOUNTS."""

import uuid
from datetime import datetime

import six
from flask import current_app, session
from flask_security import current_user
from future.utils import raise_from
from jwt import DecodeError, ExpiredSignatureError, decode, encode
from werkzeug.utils import import_string

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


def set_session_info(app, response, **extra):
    """Add X-Session-ID and X-User-ID to http response."""
    session_id = getattr(session, 'sid_s', None)
    if session_id:
        response.headers['X-Session-ID'] = session_id
    if current_user.is_authenticated:
        response.headers['X-User-ID'] = current_user.get_id()


def obj_or_import_string(value, default=None):
    """Import string or return object.

    :params value: Import path or class object to instantiate.
    :params default: Default object to return if the import fails.
    :returns: The imported object.
    """
    if isinstance(value, six.string_types):
        return import_string(value)
    elif value:
        return value
    return default


def load_or_import_from_config(key, app=None, default=None):
    """Load or import value from config.

    :returns: The loaded value.
    """
    app = app or current_app
    imp = app.config.get(key)
    return obj_or_import_string(imp, default=default)
