# SPDX-FileCopyrightText: 2015-2026 CERN.
# SPDX-FileCopyrightText: 2024-2026 Graz University of Technology.
# SPDX-FileCopyrightText: 2025 KTH Royal Institute of Technology.
# SPDX-License-Identifier: MIT

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

# Monkey patch Werkzeug 2.1
# Flask-Login uses the safe_str_cmp method which has been removed in Werkzeug
# 2.1. Flask-Login v0.6.0 (yet to be released at the time of writing) fixes the
# issue. Once we depend on Flask-Login v0.6.0 as the minimal version in
# Flask-Security-Invenio/Invenio-Accounts we can remove this patch again.
try:
    # Werkzeug <2.1
    from werkzeug import security

    security.safe_str_cmp
except AttributeError:
    # Werkzeug >=2.1
    import hmac

    from werkzeug import security

    security.safe_str_cmp = hmac.compare_digest

from .ext import InvenioAccounts, InvenioAccountsREST, InvenioAccountsUI
from .proxies import current_accounts

__version__ = "8.1.0"

__all__ = (
    "__version__",
    "current_accounts",
    "InvenioAccounts",
    "InvenioAccountsUI",
    "InvenioAccountsREST",
)
