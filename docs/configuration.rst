..
    This file is part of Invenio.
    Copyright (C) 2017 CERN.

    Invenio is free software; you can redistribute it
    and/or modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the
    Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
    MA 02111-1307, USA.

    In applying this license, CERN does not
    waive the privileges and immunities granted to it by virtue of its status
    as an Intergovernmental Organization or submit itself to any jurisdiction.


Configuration
=============

Sessions
--------

Invenio-Accounts stores users' sessions server-side via ``flask-kvsession``.

By default, Redis is used for the sessionstore.
This is configurable via the ``sessionstore`` parameter to
``InvenioAccounts``.
See the documentation for ``flask-kvsession`` for supported key-value stores.

Sessions' time to live ("TTL") is set via the ``PERMANENT_SESSION_LIFETIME``
config value (see the `flask documentation
<http://flask.pocoo.org/docs/0.12/config/#builtin-configuration-values>`_).

Variables
---------

.. automodule:: invenio_accounts.config
   :members:
