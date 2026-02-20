# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2026 CERN.
# Copyright (C) 2026 KTH Royal Institute of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Cache wrappers for invenio-accounts."""


class RoleResolverCache:
    """Simple interface to cache role reference -> role id mappings."""

    prefix = "role_id"

    def __init__(self, cache):
        """Constructor."""
        self._cache = cache

    def get(self, key):
        """Get cached value or None."""
        if self._cache is None:
            return None
        mapping = self._cache.get(self._key()) or {}
        return mapping.get(str(key))

    def set(self, key, value):
        """Set cache value."""
        if self._cache is None:
            return
        mapping = self._cache.get(self._key()) or {}
        mapping[str(key)] = value
        self._cache.set(self._key(), mapping, timeout=60 * 60 * 24)

    def clear(self):
        """Clear all cached role mappings."""
        if self._cache is None:
            return
        self._cache.delete(self._key())

    def _key(self):
        """Build key for current_cache."""
        return f"invenio_accounts:{self.prefix}"
