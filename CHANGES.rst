..
    This file is part of Invenio.
    Copyright (C) 2015-2020 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version 1.4.3 (released 2020-12-17)

- Adds theme dependent icons.

Version 1.4.2 (released 2020-12-11)

- Fixes logout from security view.

Version 1.4.1 (released 2020-12-10)

- Fixes styling of forgot password form in semantic ui theme.

Version 1.4.0 (released 2020-12-09)

- Major: adds new Semantic UI theme.
- Adds Turkish translations.
- Fixes ``next`` parameter being used in the sign-up form.
- Fixes issue with translation files causing translations not to be picked up.
- Fixes wording from sign in to log in.
- Removes password length validation during login.

Version 1.3.0 (released 2020-05-15)

- Refreshes the CSRF token on login and logout.
- Removes the example app.
- Migrate from `Flask-KVSession` to `Flask-KVSession-Invenio`, fork of
  the former.

Version 1.2.2 (released 2020-05-13)

*This release was removed from PyPI on 2020-05-15 due to issues with the
release.*

Version 1.2.1 (released 2020-04-28)

- Fixes issue with the latest WTForms v2.3.x release which now requires an
  extra library for email validation.

Version 1.2.0 (released 2020-03-09)

- Replaces Flask dependency with centrally managed invenio-base

Version 1.1.4 (released 2020-04-28)

- Fixes issue with the latest WTForms v2.3.x release which now requires an
  extra library for email validation.

Version 1.1.3 (released 2020-02-19)

- Replaces Flask-CeleryExt to invenio-celery due to version incompatibilities
  with celery, kombu. Removes Flask-BabelExt already provided by invenio-i18n

Version 1.1.2 (released 2020-02-12)

- Fixes requirements for Flask, Werkzeug and Flask-Login due to
  incompatibilities of latest released modules.

Version 1.1.1 (released 2019-03-10)

- Fixes an issue where the HTTP headers X-Session-ID and X-User-ID are added
  even if the value is not known. This causes 'None' to be logged in Nginx,
  instead of simply '-'.

Version 1.1.0 (released 2019-02-15)

- Added support for for adding the user id and session id of the current user
  into the HTTP headers (``X-User-ID`` and ``X-Session-ID``) for upstream
  servers to use. For instance, this way current user/session ids can be logged
  by Nginx into the web server access logs. The feature is off by default and
  can be enabled via the ``ACCOUNTS_USERINFO_HEADERS`` configuration variable.
  Note: The upstream server should strip the two headers from the response
  returned to the client. The purpose is purely to allow upstream proxies like
  Nginx to log the user/session id for a specific request.

- Changed token expiration from 5 days to 30 minutes for the password reset
  token and email confirmation token. Using the tokens will as a side-effect
  login in the user, which means that if the link is leaked (e.g. forwarded by
  the users themselves), then another person can use the link to access the
  account. Flask-Security v3.1.0 addresses this issue, but has not yet been
  released.

- Fixes issue that could rehash the user password in the adminstration
  interface.

Version 1.0.2 (released 2018-10-31)

- Added AnonymousIdentity loader to app initialisation to fix the ``any_user``
  Need in Invenio-Access.

Version 1.0.1 (released 2018-05-25)

- Bumped Flask-CeleryExt from v0.3.0 to v0.3.1 to fix issue with Celery version
  string not being parsable and thus causing problems with installing Celery.

Version 1.0.0 (released 2018-03-23)

- Initial public release.
