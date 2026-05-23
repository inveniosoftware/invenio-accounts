# SPDX-FileCopyrightText: 2017-2018 CERN.
# SPDX-License-Identifier: MIT

"""JWT context processors."""

from flask import current_app, render_template
from markupsafe import Markup

from ..proxies import current_accounts


def jwt_proccessor():
    """Context processor for jwt."""

    def jwt():
        """Context processor function to generate jwt."""
        token = current_accounts.jwt_creation_factory()
        return Markup(
            render_template(
                current_app.config["ACCOUNTS_JWT_DOM_TOKEN_TEMPLATE"], token=token
            )
        )

    def jwt_token():
        """Context processor function to generate jwt."""
        return current_accounts.jwt_creation_factory()

    return {
        "jwt": jwt,
        "jwt_token": jwt_token,
    }
