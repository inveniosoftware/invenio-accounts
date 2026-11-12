# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-License-Identifier: MIT

"""JS/CSS Webpack bundles for Invenio-Accounts."""

from invenio_assets.webpack import WebpackThemeBundle

accounts = WebpackThemeBundle(
    __name__,
    "assets",
    default="semantic-ui",
    themes={
        "semantic-ui": dict(
            entry={
                "invenio-accounts-altcha": "./js/invenio_accounts/altcha.js",
            },
            dependencies={
                "altcha": "^3.5.0",
            },
            aliases={"@js/invenio_accounts": "js/invenio_accounts"},
        ),
    },
)
