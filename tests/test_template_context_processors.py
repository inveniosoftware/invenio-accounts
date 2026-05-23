# SPDX-FileCopyrightText: 2017-2018 CERN.
# SPDX-License-Identifier: MIT


"""Tests for template context processors."""

from flask import render_template_string


def test_context_processor_jwt(app):
    """Test context processor JWT."""
    template = r"""
    {{ jwt() }}
    """
    with app.test_request_context():
        html = render_template_string(template)
        assert "authorized_token" in html


def test_context_processor_jwt_token(app):
    """Test context processor token JWT."""
    template = r"""
    {{ jwt_token() }}
    """
    with app.test_request_context():
        html = render_template_string(template)
        assert html
