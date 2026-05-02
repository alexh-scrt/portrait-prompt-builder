"""Flask test client integration tests for the Portrait Prompt Builder routes.

Covers:
- GET / returns 200 and correct content
- POST /generate with valid data returns 200 and prompt content
- POST /generate with invalid data returns 400 and error messaging
- GET /about redirects or returns a valid response
- Edge cases: missing fields, oversized inputs, all presets, all decades
"""

from __future__ import annotations

import pytest
from flask import Flask
from flask.testing import FlaskClient

from portrait_prompt_builder import create_app
from portrait_prompt_builder.presets import ALL_PRESETS
from portrait_prompt_builder.prompt_engine import VALID_DECADES, VALID_MOODS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def app() -> Flask:
    """Create a Flask app configured for testing."""
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "WTF_CSRF_ENABLED": False,
        }
    )


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    """Return a test client for the Flask app."""
    return app.test_client()


# ---------------------------------------------------------------------------
# Minimal valid POST payload
# ---------------------------------------------------------------------------

MINIMAL_FORM_DATA: dict = {
    "decade": "1980s",
    "setting": "a sunny suburban kitchen with yellow wallpaper",
    "clothing": "a striped polo shirt and corduroy trousers",
    "mood": "happy",
    "preset_id": "warm_kodak_film",
}

FULL_FORM_DATA: dict = {
    "decade": "1990s",
    "setting": "a school playground with climbing frames",
    "clothing": "dungarees and a graphic tee",
    "mood": "playful",
    "preset_id": "golden_hour",
    "gender": "girl",
    "age": "9",
    "features": "curly red hair and freckles",
    "camera_style": "medium format film, slightly overexposed",
}


def _make_form(**overrides) -> dict:
    """Return a copy of MINIMAL_FORM_DATA with overrides applied."""
    data = dict(MINIMAL_FORM_DATA)
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# Tests: GET /
# ---------------------------------------------------------------------------


class TestIndexRoute:
    """Tests for the GET / route."""

    def test_get_index_returns_200(self, client: FlaskClient) -> None:
        response = client.get("/")
        assert response.status_code == 200

    def test_get_index_content_type_is_html(self, client: FlaskClient) -> None:
        response = client.get("/")
        assert "text/html" in response.content_type

    def test_get_index_response_is_not_empty(self, client: FlaskClient) -> None:
        response = client.get("/")
        assert len(response.data) > 0

    def test_get_index_contains_form_element(self, client: FlaskClient) -> None:
        response = client.get("/")
        body = response.data.decode("utf-8")
        assert "<form" in body.lower()

    def test_get_index_contains_preset_options(self, client: FlaskClient) -> None:
        response = client.get("/")
        body = response.data.decode("utf-8")
        # At least one preset id should appear in the rendered HTML
        assert any(preset["id"] in body for preset in ALL_PRESETS)

    def test_get_index_contains_decade_options(self, client: FlaskClient) -> None:
        response = client.get("/")
        body = response.data.decode("utf-8")
        assert "1980s" in body or "1990s" in body


# ---------------------------------------------------------------------------
# Tests: POST /generate — valid inputs
# ---------------------------------------------------------------------------


class TestGenerateRouteValid:
    """Tests for the POST /generate route with valid form data."""

    def test_post_generate_minimal_returns_200(self, client: FlaskClient) -> None:
        response = client.post("/generate", data=MINIMAL_FORM_DATA)
        assert response.status_code == 200

    def test_post_generate_full_returns_200(self, client: FlaskClient) -> None:
        response = client.post("/generate", data=FULL_FORM_DATA)
        assert response.status_code == 200

    def test_post_generate_response_is_html(self, client: FlaskClient) -> None:
        response = client.post("/generate", data=MINIMAL_FORM_DATA)
        assert "text/html" in response.content_type

    def test_post_generate_contains_decade_in_body(self, client: FlaskClient) -> None:
        response = client.post("/generate", data=MINIMAL_FORM_DATA)
        body = response.data.decode("utf-8")
        assert "1980s" in body

    def test_post_generate_contains_preset_label(self, client: FlaskClient) -> None:
        response = client.post("/generate", data=MINIMAL_FORM_DATA)
        body = response.data.decode("utf-8")
        assert "Warm Kodak Film" in body

    def test_post_generate_contains_childhood_reference(self, client: FlaskClient) -> None:
        response = client.post("/generate", data=MINIMAL_FORM_DATA)
        body = response.data.decode("utf-8")
        assert "childhood" in body.lower() or "portrait" in body.lower()

    def test_post_generate_full_contains_features(self, client: FlaskClient) -> None:
        response = client.post("/generate", data=FULL_FORM_DATA)
        body = response.data.decode("utf-8")
        assert "curly red hair" in body

    def test_post_generate_full_contains_setting_fragment(self, client: FlaskClient) -> None:
        response = client.post("/generate", data=FULL_FORM_DATA)
        body = response.data.decode("utf-8")
        assert "playground" in body

    def test_post_generate_response_is_not_empty(self, client: FlaskClient) -> None:
        response = client.post("/generate", data=MINIMAL_FORM_DATA)
        assert len(response.data) > 200

    @pytest.mark.parametrize("preset", ALL_PRESETS, ids=[p["id"] for p in ALL_PRESETS])
    def test_each_preset_returns_200(self, client: FlaskClient, preset: dict) -> None:
        data = _make_form(preset_id=preset["id"])
        response = client.post("/generate", data=data)
        assert response.status_code == 200

    @pytest.mark.parametrize("decade", sorted(VALID_DECADES))
    def test_each_decade_returns_200(self, client: FlaskClient, decade: str) -> None:
        data = _make_form(decade=decade)
        response = client.post("/generate", data=data)
        assert response.status_code == 200

    @pytest.mark.parametrize("mood", sorted(VALID_MOODS))
    def test_each_mood_returns_200(self, client: FlaskClient, mood: str) -> None:
        data = _make_form(mood=mood)
        response = client.post("/generate", data=data)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Tests: POST /generate — invalid inputs
# ---------------------------------------------------------------------------


class TestGenerateRouteInvalid:
    """Tests for the POST /generate route with invalid form data."""

    def test_empty_post_returns_400(self, client: FlaskClient) -> None:
        response = client.post("/generate", data={})
        assert response.status_code == 400

    def test_missing_decade_returns_400(self, client: FlaskClient) -> None:
        data = _make_form(decade="")
        response = client.post("/generate", data=data)
        assert response.status_code == 400

    def test_missing_setting_returns_400(self, client: FlaskClient) -> None:
        data = _make_form(setting="")
        response = client.post("/generate", data=data)
        assert response.status_code == 400

    def test_missing_clothing_returns_400(self, client: FlaskClient) -> None:
        data = _make_form(clothing="")
        response = client.post("/generate", data=data)
        assert response.status_code == 400

    def test_missing_mood_returns_400(self, client: FlaskClient) -> None:
        data = _make_form(mood="")
        response = client.post("/generate", data=data)
        assert response.status_code == 400

    def test_missing_preset_id_returns_400(self, client: FlaskClient) -> None:
        data = _make_form(preset_id="")
        response = client.post("/generate", data=data)
        assert response.status_code == 400

    def test_invalid_decade_returns_400(self, client: FlaskClient) -> None:
        data = _make_form(decade="1850s")
        response = client.post("/generate", data=data)
        assert response.status_code == 400

    def test_invalid_mood_returns_400(self, client: FlaskClient) -> None:
        data = _make_form(mood="ecstatic")
        response = client.post("/generate", data=data)
        assert response.status_code == 400

    def test_invalid_preset_id_returns_400(self, client: FlaskClient) -> None:
        data = _make_form(preset_id="nonexistent_preset")
        response = client.post("/generate", data=data)
        assert response.status_code == 400

    def test_invalid_inputs_response_contains_error_indication(self, client: FlaskClient) -> None:
        """The response body for invalid inputs should still serve the form page."""
        data = _make_form(decade="")
        response = client.post("/generate", data=data)
        body = response.data.decode("utf-8")
        # Should re-render the form (which contains a <form> element)
        assert "<form" in body.lower() or "error" in body.lower()

    def test_oversized_setting_returns_400(self, client: FlaskClient) -> None:
        data = _make_form(setting="x" * 201)
        response = client.post("/generate", data=data)
        assert response.status_code == 400

    def test_oversized_clothing_returns_400(self, client: FlaskClient) -> None:
        data = _make_form(clothing="y" * 201)
        response = client.post("/generate", data=data)
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Tests: GET /about
# ---------------------------------------------------------------------------


class TestAboutRoute:
    """Tests for the GET /about route."""

    def test_about_returns_2xx_or_3xx(self, client: FlaskClient) -> None:
        """About page should either render (2xx) or redirect (3xx) gracefully."""
        response = client.get("/about", follow_redirects=False)
        assert response.status_code in (200, 301, 302, 303, 307, 308)

    def test_about_with_follow_redirects_returns_200(self, client: FlaskClient) -> None:
        response = client.get("/about", follow_redirects=True)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Tests: 404 handling
# ---------------------------------------------------------------------------


class TestErrorHandlers:
    """Tests for Flask error handlers."""

    def test_unknown_route_returns_404(self, client: FlaskClient) -> None:
        response = client.get("/this-path-does-not-exist")
        assert response.status_code == 404

    def test_404_response_is_not_empty(self, client: FlaskClient) -> None:
        response = client.get("/nonexistent")
        assert len(response.data) > 0


# ---------------------------------------------------------------------------
# Tests: app factory configuration
# ---------------------------------------------------------------------------


class TestAppFactory:
    """Tests for the create_app factory function."""

    def test_create_app_returns_flask_instance(self) -> None:
        from flask import Flask
        from portrait_prompt_builder import create_app

        app = create_app({"TESTING": True, "SECRET_KEY": "test"})
        assert isinstance(app, Flask)

    def test_testing_config_is_applied(self) -> None:
        from portrait_prompt_builder import create_app

        app = create_app({"TESTING": True, "SECRET_KEY": "test"})
        assert app.config["TESTING"] is True

    def test_default_config_testing_is_false(self) -> None:
        from portrait_prompt_builder import create_app

        app = create_app()
        assert app.config["TESTING"] is False

    def test_custom_secret_key_is_applied(self) -> None:
        from portrait_prompt_builder import create_app

        app = create_app({"SECRET_KEY": "my-custom-key"})
        assert app.config["SECRET_KEY"] == "my-custom-key"

    def test_app_has_index_route(self, app: Flask) -> None:
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert "/" in rules

    def test_app_has_generate_route(self, app: Flask) -> None:
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert "/generate" in rules

    def test_app_has_about_route(self, app: Flask) -> None:
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert "/about" in rules

    def test_generate_route_only_accepts_post(self, client: FlaskClient) -> None:
        response = client.get("/generate")
        assert response.status_code == 405
