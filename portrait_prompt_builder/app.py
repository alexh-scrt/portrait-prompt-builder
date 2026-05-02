"""Flask application factory and route definitions for the Portrait Prompt Builder.

This module contains the ``build_app`` factory function that creates and
configures the Flask application instance, as well as all route handlers:

- ``GET /`` — renders the guided multi-step portrait form (``index.html``).
- ``POST /generate`` — accepts form data, assembles the prompt via
  :func:`~portrait_prompt_builder.prompt_engine.build_prompt`, and renders
  the result page (``result.html``).
- ``GET /about`` — optional lightweight about/help page.

All template rendering uses the Jinja2 templates in the ``templates/``
package directory, and static assets are served from ``static/``.
"""

from __future__ import annotations

import os
from typing import Any

from flask import Flask, render_template, request, redirect, url_for, flash

from portrait_prompt_builder.presets import list_presets, preset_choices
from portrait_prompt_builder.prompt_engine import (
    build_prompt,
    get_prompt_metadata,
    validate_inputs,
    VALID_DECADES,
    VALID_MOODS,
    VALID_GENDERS,
)


def build_app(test_config: dict[str, Any] | None = None) -> Flask:
    """Create and configure the Flask application instance.

    This factory function is the single source of truth for application
    construction.  It is called by the public :func:`portrait_prompt_builder.create_app`
    entry-point and by the pytest fixtures in the test suite.

    Args:
        test_config: Optional mapping of Flask configuration overrides.
            When provided (e.g. from test fixtures), these values replace
            the defaults set here.  Typical test overrides::

                {"TESTING": True, "SECRET_KEY": "test-secret", "WTF_CSRF_ENABLED": False}

    Returns:
        A fully initialised :class:`flask.Flask` application ready to
        serve requests.

    Example::

        >>> from portrait_prompt_builder.app import build_app
        >>> app = build_app()
        >>> app.testing
        False
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # ------------------------------------------------------------------
    # Default configuration
    # ------------------------------------------------------------------
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-in-production"),
        TESTING=False,
        # Maximum content length for form submissions (1 MB)
        MAX_CONTENT_LENGTH=1 * 1024 * 1024,
    )

    if test_config is not None:
        # Override defaults with any test-supplied values.
        app.config.from_mapping(test_config)

    # ------------------------------------------------------------------
    # Register routes
    # ------------------------------------------------------------------
    _register_routes(app)

    return app


def _register_routes(app: Flask) -> None:
    """Attach all URL rules to *app*.

    Separated from :func:`build_app` to keep the factory function concise
    and to allow routes to be tested in isolation if needed.

    Args:
        app: The Flask application instance to register routes on.
    """

    # ------------------------------------------------------------------
    # Context helpers
    # ------------------------------------------------------------------

    def _common_form_context() -> dict[str, Any]:
        """Return template context variables shared by the form pages."""
        return {
            "presets": list_presets(),
            "preset_choices": preset_choices(),
            "valid_decades": sorted(VALID_DECADES),
            "valid_moods": sorted(VALID_MOODS),
            "valid_genders": sorted(VALID_GENDERS),
        }

    # ------------------------------------------------------------------
    # GET / — main form page
    # ------------------------------------------------------------------

    @app.route("/", methods=["GET"])
    def index() -> str:
        """Render the guided multi-step portrait form.

        Returns:
            Rendered HTML of ``index.html`` with all preset and field
            option data injected into the template context.
        """
        context = _common_form_context()
        return render_template("index.html", **context)

    # ------------------------------------------------------------------
    # POST /generate — prompt generation endpoint
    # ------------------------------------------------------------------

    @app.route("/generate", methods=["POST"])
    def generate() -> Any:
        """Accept form data, build the prompt, and render the result page.

        Reads all expected fields from ``request.form``, validates them via
        :func:`~portrait_prompt_builder.prompt_engine.validate_inputs`, and
        on success renders ``result.html`` with the assembled prompt and
        accompanying metadata.

        On validation failure the user is redirected back to the form with
        flash messages describing the specific field errors.

        Returns:
            On success: rendered HTML of ``result.html``.
            On failure: redirect to ``index`` with flash error messages.
        """
        # Collect all expected form fields
        inputs: dict[str, Any] = {
            "decade": request.form.get("decade", "").strip(),
            "setting": request.form.get("setting", "").strip(),
            "clothing": request.form.get("clothing", "").strip(),
            "mood": request.form.get("mood", "").strip(),
            "preset_id": request.form.get("preset_id", "").strip(),
            "gender": request.form.get("gender", "").strip(),
            "age": request.form.get("age", "").strip(),
            "features": request.form.get("features", "").strip(),
            "camera_style": request.form.get("camera_style", "").strip(),
        }

        # Validate before attempting to build
        errors = validate_inputs(inputs)
        if errors:
            for error in errors:
                flash(error, category="error")
            # Re-render the form (not a redirect) so we can preserve form
            # state in the template context.
            context = _common_form_context()
            context["form_data"] = inputs
            context["errors"] = errors
            return render_template("index.html", **context), 400

        # Build the prompt — should not raise since we validated above, but
        # catch defensively to avoid unhandled 500 errors.
        try:
            prompt = build_prompt(inputs)
            metadata = get_prompt_metadata(inputs)
        except ValueError as exc:
            flash(str(exc), category="error")
            context = _common_form_context()
            context["form_data"] = inputs
            return render_template("index.html", **context), 400

        # Resolve the preset object for display on the result page
        from portrait_prompt_builder.presets import get_preset  # local to avoid circular at module level
        preset = get_preset(inputs["preset_id"])

        return render_template(
            "result.html",
            prompt=prompt,
            metadata=metadata,
            preset=preset,
            inputs=inputs,
        )

    # ------------------------------------------------------------------
    # GET /about — lightweight help page
    # ------------------------------------------------------------------

    @app.route("/about", methods=["GET"])
    def about() -> str:
        """Render the about/help page.

        Returns:
            Rendered HTML of ``about.html`` if it exists, otherwise a
            simple redirect to the index page.
        """
        # The about template is created in a later phase; fall back
        # gracefully if it is not yet present.
        try:
            return render_template("about.html")
        except Exception:
            return redirect(url_for("index"))

    # ------------------------------------------------------------------
    # Error handlers
    # ------------------------------------------------------------------

    @app.errorhandler(404)
    def not_found(error: Exception) -> tuple[str, int]:
        """Handle 404 Not Found errors.

        Args:
            error: The exception raised by Flask.

        Returns:
            Tuple of (rendered HTML, status code).
        """
        return render_template("404.html") if _template_exists(app, "404.html") else (
            "<h1>404 — Page Not Found</h1><p><a href='/'>Return home</a></p>",
            404,
        )

    @app.errorhandler(413)
    def request_too_large(error: Exception) -> tuple[str, int]:
        """Handle 413 Request Entity Too Large errors.

        Args:
            error: The exception raised by Flask.

        Returns:
            Tuple of (rendered HTML, status code).
        """
        flash("Your submission was too large. Please shorten your inputs.", category="error")
        return redirect(url_for("index")), 413

    @app.errorhandler(500)
    def internal_error(error: Exception) -> tuple[str, int]:
        """Handle unexpected 500 Internal Server Error responses.

        Args:
            error: The exception raised by Flask.

        Returns:
            Tuple of (rendered HTML, status code).
        """
        return render_template("500.html") if _template_exists(app, "500.html") else (
            "<h1>500 — Internal Server Error</h1><p><a href='/'>Return home</a></p>",
            500,
        )


def _template_exists(app: Flask, template_name: str) -> bool:
    """Check whether a named template file exists in the app's template folder.

    Args:
        app: The Flask application whose template folder is searched.
        template_name: Filename of the template to look up (e.g.
            ``"404.html"``).

    Returns:
        ``True`` if the template file is present on disk, ``False``
        otherwise.
    """
    import os
    template_path = os.path.join(app.template_folder or "templates", template_name)  # type: ignore[arg-type]
    # Resolve relative to the app's root path when not absolute
    if not os.path.isabs(template_path):
        template_path = os.path.join(app.root_path, template_path)
    return os.path.isfile(template_path)


__all__ = ["build_app"]
