# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
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

"""Invenio user management and authentication.

Adminstration interface
-----------------------
You can view and manage users and roles via the administration interface. Below
is a screenshot from the user creation:

.. image:: admin.png

Command-line interface
----------------------
Users and roles can be created via the CLI. Below is a simple example of
creating a user, a role and assining the user to the role:

.. code-block:: console

    $ flask users create --active info@inveniosoftware.org
    $ flask roles create admins
    $ flask roles add info@inveniosoftware.org admins

You can also e.g. deactive users:

.. code-block:: console

    $ flask users deactivate info@inveniosoftware.org
"""

from __future__ import absolute_import, print_function

from .ext import InvenioAccounts, InvenioAccountsUI, InvenioAccountsREST
from .proxies import current_accounts
from .version import __version__

__all__ = (
    '__version__',
    'current_accounts',
    'InvenioAccounts',
    'InvenioAccountsUI',
    'InvenioAccountsREST',
)
