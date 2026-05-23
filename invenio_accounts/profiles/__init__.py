# SPDX-FileCopyrightText: 2022 TU Wien.
# SPDX-License-Identifier: MIT

"""Utilities for validation of user profiles and preferences."""

from .dicts import UserPreferenceDict, UserProfileDict, ValidatedDict
from .schemas import UserPreferencesSchema, UserProfileSchema

__all__ = (
    "UserPreferenceDict",
    "UserPreferencesSchema",
    "UserProfileDict",
    "UserProfileSchema",
    "ValidatedDict",
)
