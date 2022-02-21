# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2022 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Schemas for user profiles and preferences."""


from marshmallow import Schema, fields


class UserProfileSchema(Schema):
    """The default user profile schema."""

    full_name = fields.String()


class UserPreferencesSchema(Schema):
    """The default schema for user preferences."""
