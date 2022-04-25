# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""API objects for Invenio Accounts."""

from collections import defaultdict


class DBUsersChangeHistory:
    """DB Users change history storage."""

    def __init__(self):
        """constructor."""
        # the keys are going to be the sessions, the values are going to be
        # the sets of dirty/deleted models
        self.updated_users = defaultdict(lambda: list())
        self.updated_roles = defaultdict(lambda: list())
        self.deleted_users = defaultdict(lambda: list())
        self.deleted_roles = defaultdict(lambda: list())

    def _clear_dirty_sets(self, session):
        """Clear the dirty sets for the given session."""
        sid = id(session)
        self.updated_users.pop(sid, None)
        self.updated_roles.pop(sid, None)
        self.deleted_users.pop(sid, None)
        self.deleted_roles.pop(sid, None)
