=========================
 Invenio-Accounts v0.1.2
=========================

Invenio-Accounts v0.1.2 was released on September 3, 2015.

About
-----

Invenio module for managing user accounts.

*This is an experimental development preview release.*

Incompatible changes
--------------------

- Changes way how the access tokens are generated from "mailcookie" to
  tokens using "itsdangerous" package.  (#7)
- Removes support for local access configuration and the automatic SSO
  logout url rediction.  (#8)

New features
------------

- Adds module for generating time limited tokens for password
  recovery.  (#7)

Bug fixes
---------

- Changes index name definition in `UserEXT` model for `id_user` and
  `method` columns.  (#5)

Installation
------------

   $ pip install invenio-accounts==0.1.2

Documentation
-------------

   http://invenio-accounts.readthedocs.org/en/v0.1.2

Happy hacking and thanks for flying Invenio-Accounts.

| Invenio Development Team
|   Email: info@invenio-software.org
|   IRC: #invenio on irc.freenode.net
|   Twitter: http://twitter.com/inveniosoftware
|   GitHub: https://github.com/inveniosoftware/invenio-accounts
|   URL: http://invenio-software.org
