Installation
============


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
config value (see the flask documentation).
