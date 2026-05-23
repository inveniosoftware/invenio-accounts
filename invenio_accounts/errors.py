# SPDX-FileCopyrightText: 2017-2018 CERN.
# SPDX-License-Identifier: MIT

"""Exception classes."""


class JWTExtendedException(Exception):
    """Base exception for all JWT errors."""


class JWTDecodeError(JWTExtendedException):
    """Exception raised when decoding is failed."""


class JWTExpiredToken(JWTExtendedException):
    """Exception raised when JWT is expired."""


class AlreadyLinkedError(Exception):
    """Signifies that an account was already linked to another account."""

    def __init__(self, user, external_id):
        """Initialize exception."""
        self.user = user
        self.external_id = external_id
