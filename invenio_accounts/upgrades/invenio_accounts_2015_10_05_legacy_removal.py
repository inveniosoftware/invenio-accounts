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

"""Remove legacy upgrade recipes."""

import warnings

from invenio_ext.sqlalchemy import db
from invenio_upgrader.api import op

from sqlalchemy.sql import text

depends_on = []

legacy_upgrades = [
    'accounts_2014_11_07_usergroup_name_column_unique',
]


def info():
    """Info message."""
    return __doc__


def do_upgrade():
    """Implement your upgrades here."""
    sql = text('delete from upgrade where upgrade = :upgrade')
    for upgrade in legacy_upgrades:
        db.engine.execute(sql, upgrade=upgrade)


def estimate():
    """Estimate running time of upgrade in seconds (optional)."""
    return 1


def pre_upgrade():
    """Run pre-upgrade checks (optional)."""
    sql = text('select 1 from upgrade where upgrade = :upgrade')
    for upgrade in legacy_upgrades:
        if not db.engine.execute(sql, upgrade=upgrade).fetchall():
            warnings.warn("Upgrade '{}' was not applied.".format(upgrade))


def post_upgrade():
    """Run post-upgrade checks (optional)."""
    # Example of issuing warnings:
    # warnings.warn("A continuable error occurred")
