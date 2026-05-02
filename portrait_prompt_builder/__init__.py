"""portrait_prompt_builder package.

Exposes the Flask application factory ``create_app`` so that the package
can be used both as a standalone runnable module and as an importable
library in tests and other tooling.

Example usage::

    from portrait_prompt_builder import create_app

    app = create_app()
    app.run(debug=True)

Running directly::

    python -m flask --app portrait_prompt_builder run
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from flask import Flask


def create_app(test_config: dict[str, Any] | None = None) -> "Flask":
    """Application factory for the Portrait Prompt Builder Flask app.

    Creates and configures a Flask application instance.  All route
    registrations, template configuration, and extension initialisation
    are delegated to :mod:`portrait_prompt_builder.app` so that this
    factory remains a thin, stable public entry-point.

    Args:
        test_config: Optional mapping of configuration values to override
            the default application configuration.  Useful for injecting
            test-specific settings (e.g. ``TESTING=True``,
            ``SECRET_KEY='test'``) without touching environment variables.

    Returns:
        A fully configured :class:`flask.Flask` application instance
        ready to handle requests.

    Raises:
        ImportError: If the internal ``app`` module cannot be imported
            (indicates a broken installation).

    Example::

        >>> from portrait_prompt_builder import create_app
        >>> app = create_app({"TESTING": True, "SECRET_KEY": "test"})
        >>> app.testing
        True
    """
    from portrait_prompt_builder.app import build_app  # noqa: PLC0415

    return build_app(test_config=test_config)


__all__ = ["create_app"]
