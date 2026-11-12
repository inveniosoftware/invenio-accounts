# SPDX-FileCopyrightText: 2017-2026 CERN.
# SPDX-FileCopyrightText: 2021 TU Wien.
# SPDX-License-Identifier: MIT

"""Invenio-accounts views."""

from .settings import forgot_password, login

__all__ = (
    "forgot_password",
    "login",
)
