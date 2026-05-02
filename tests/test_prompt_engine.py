"""Unit tests for portrait_prompt_builder.prompt_engine module.

Covers validation, normalisation, individual section builders (via the
public :func:`build_prompt` output), and the :func:`get_prompt_metadata`
helper across various input combinations and all five style presets.
"""

from __future__ import annotations

import pytest

from portrait_prompt_builder.prompt_engine import (
    VALID_DECADES,
    VALID_GENDERS,
    VALID_MOODS,
    build_prompt,
    get_prompt_metadata,
    normalise_inputs,
    validate_inputs,
)
from portrait_prompt_builder.presets import ALL_PRESETS

# ---------------------------------------------------------------------------
# Minimal valid input fixture
# ---------------------------------------------------------------------------

MINIMAL_VALID: dict = {
    "decade": "1980s",
    "setting": "a sunny suburban kitchen with yellow wallpaper",
    "clothing": "a striped polo shirt and corduroy trousers",
    "mood": "happy",
    "preset_id": "warm_kodak_film",
}

FULL_VALID: dict = {
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_inputs(**overrides) -> dict:
    """Return a copy of MINIMAL_VALID with the given key overrides applied."""
    data = dict(MINIMAL_VALID)
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# Tests: VALID_* constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Sanity checks for the exported constant sets."""

    def test_valid_decades_is_frozenset(self) -> None:
        assert isinstance(VALID_DECADES, frozenset)

    def test_valid_decades_contains_expected(self) -> None:
        for decade in ["1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s"]:
            assert decade in VALID_DECADES, f"{decade} missing from VALID_DECADES"

    def test_valid_moods_is_frozenset(self) -> None:
        assert isinstance(VALID_MOODS, frozenset)

    def test_valid_moods_contains_expected(self) -> None:
        expected = {"happy", "curious", "dreamy", "melancholic", "playful", "serious", "adventurous", "shy"}
        assert expected <= VALID_MOODS

    def test_valid_genders_is_frozenset(self) -> None:
        assert isinstance(VALID_GENDERS, frozenset)

    def test_valid_genders_contains_expected(self) -> None:
        assert {"boy", "girl", "child"} <= VALID_GENDERS


# ---------------------------------------------------------------------------
# Tests: validate_inputs
# ---------------------------------------------------------------------------


class TestValidateInputs:
    """Tests for the validate_inputs() function."""

    def test_valid_minimal_inputs_returns_empty_list(self) -> None:
        errors = validate_inputs(MINIMAL_VALID)
        assert errors == []

    def test_valid_full_inputs_returns_empty_list(self) -> None:
        errors = validate_inputs(FULL_VALID)
        assert errors == []

    def test_empty_dict_returns_errors(self) -> None:
        errors = validate_inputs({})
        assert len(errors) > 0

    def test_missing_decade_returns_error(self) -> None:
        data = _make_inputs(decade="")
        errors = validate_inputs(data)
        assert any("decade" in e for e in errors)

    def test_missing_setting_returns_error(self) -> None:
        data = _make_inputs(setting="")
        errors = validate_inputs(data)
        assert any("setting" in e for e in errors)

    def test_missing_clothing_returns_error(self) -> None:
        data = _make_inputs(clothing="")
        errors = validate_inputs(data)
        assert any("clothing" in e for e in errors)

    def test_missing_mood_returns_error(self) -> None:
        data = _make_inputs(mood="")
        errors = validate_inputs(data)
        assert any("mood" in e for e in errors)

    def test_missing_preset_id_returns_error(self) -> None:
        data = _make_inputs(preset_id="")
        errors = validate_inputs(data)
        assert any("preset_id" in e for e in errors)

    def test_invalid_decade_returns_error(self) -> None:
        data = _make_inputs(decade="1850s")
        errors = validate_inputs(data)
        assert any("decade" in e.lower() or "1850s" in e for e in errors)

    def test_invalid_mood_returns_error(self) -> None:
        data = _make_inputs(mood="ecstatic")
        errors = validate_inputs(data)
        assert any("ecstatic" in e or "mood" in e.lower() for e in errors)

    def test_invalid_gender_returns_error(self) -> None:
        data = _make_inputs(gender="alien")
        errors = validate_inputs(data)
        assert any("gender" in e.lower() or "alien" in e for e in errors)

    def test_invalid_preset_id_returns_error(self) -> None:
        data = _make_inputs(preset_id="nonexistent_preset")
        errors = validate_inputs(data)
        assert any("nonexistent_preset" in e or "preset" in e.lower() for e in errors)

    def test_setting_too_long_returns_error(self) -> None:
        data = _make_inputs(setting="x" * 201)
        errors = validate_inputs(data)
        assert any("setting" in e for e in errors)

    def test_clothing_too_long_returns_error(self) -> None:
        data = _make_inputs(clothing="y" * 201)
        errors = validate_inputs(data)
        assert any("clothing" in e for e in errors)

    def test_returns_list_type(self) -> None:
        result = validate_inputs(MINIMAL_VALID)
        assert isinstance(result, list)

    def test_all_required_fields_missing_produces_multiple_errors(self) -> None:
        errors = validate_inputs({})
        # Should have at least one error per required field
        assert len(errors) >= len(["decade", "setting", "clothing", "mood", "preset_id"])

    def test_whitespace_only_decade_is_invalid(self) -> None:
        data = _make_inputs(decade="   ")
        errors = validate_inputs(data)
        assert any("decade" in e for e in errors)

    @pytest.mark.parametrize("decade", sorted(VALID_DECADES))
    def test_all_valid_decades_accepted(self, decade: str) -> None:
        data = _make_inputs(decade=decade)
        errors = validate_inputs(data)
        decade_errors = [e for e in errors if "decade" in e.lower()]
        assert decade_errors == [], f"Unexpected error for decade {decade!r}: {decade_errors}"

    @pytest.mark.parametrize("mood", sorted(VALID_MOODS))
    def test_all_valid_moods_accepted(self, mood: str) -> None:
        data = _make_inputs(mood=mood)
        errors = validate_inputs(data)
        mood_errors = [e for e in errors if "mood" in e.lower()]
        assert mood_errors == [], f"Unexpected error for mood {mood!r}: {mood_errors}"

    @pytest.mark.parametrize("preset", ALL_PRESETS, ids=[p["id"] for p in ALL_PRESETS])
    def test_all_valid_preset_ids_accepted(self, preset: dict) -> None:
        data = _make_inputs(preset_id=preset["id"])
        errors = validate_inputs(data)
        preset_errors = [e for e in errors if "preset" in e.lower()]
        assert preset_errors == [], f"Unexpected error for preset {preset['id']!r}: {preset_errors}"


# ---------------------------------------------------------------------------
# Tests: normalise_inputs
# ---------------------------------------------------------------------------


class TestNormaliseInputs:
    """Tests for the normalise_inputs() function."""

    def test_strips_whitespace_from_decade(self) -> None:
        result = normalise_inputs({"decade": "  1980s  "})
        assert result["decade"] == "1980s"

    def test_strips_whitespace_from_setting(self) -> None:
        result = normalise_inputs({"setting": "  a sunny garden  "})
        assert result["setting"] == "a sunny garden"

    def test_lowercases_mood(self) -> None:
        result = normalise_inputs({"mood": "HAPPY"})
        assert result["mood"] == "happy"

    def test_lowercases_gender(self) -> None:
        result = normalise_inputs({"gender": "GIRL"})
        assert result["gender"] == "girl"

    def test_default_gender_is_child(self) -> None:
        result = normalise_inputs({})
        assert result["gender"] == "child"

    def test_default_age_is_young(self) -> None:
        result = normalise_inputs({})
        assert result["age"] == "young"

    def test_explicit_age_is_preserved(self) -> None:
        result = normalise_inputs({"age": "10"})
        assert result["age"] == "10"

    def test_does_not_mutate_original_dict(self) -> None:
        original = {"decade": "  1970s  ", "mood": "DREAMY"}
        original_copy = dict(original)
        normalise_inputs(original)
        assert original == original_copy

    def test_returns_dict(self) -> None:
        result = normalise_inputs(MINIMAL_VALID)
        assert isinstance(result, dict)

    def test_strips_whitespace_from_features(self) -> None:
        result = normalise_inputs({"features": "  blue eyes  "})
        assert result["features"] == "blue eyes"

    def test_empty_features_returns_empty_string(self) -> None:
        result = normalise_inputs({})
        assert result["features"] == ""


# ---------------------------------------------------------------------------
# Tests: build_prompt — return type and basic content
# ---------------------------------------------------------------------------


class TestBuildPromptBasic:
    """Basic contract tests for build_prompt()."""

    def test_returns_string(self) -> None:
        result = build_prompt(MINIMAL_VALID)
        assert isinstance(result, str)

    def test_returns_non_empty_string(self) -> None:
        result = build_prompt(MINIMAL_VALID)
        assert result.strip() != ""

    def test_prompt_contains_decade(self) -> None:
        result = build_prompt(MINIMAL_VALID)
        assert "1980s" in result

    def test_prompt_contains_setting(self) -> None:
        result = build_prompt(_make_inputs(setting="a moonlit beach"))
        assert "moonlit beach" in result

    def test_prompt_contains_clothing_fragment(self) -> None:
        result = build_prompt(_make_inputs(clothing="a red raincoat"))
        assert "red raincoat" in result

    def test_prompt_contains_preset_label(self) -> None:
        result = build_prompt(MINIMAL_VALID)
        # warm_kodak_film label is 'Warm Kodak Film'
        assert "Warm Kodak Film" in result

    def test_prompt_contains_childhood_reference(self) -> None:
        result = build_prompt(MINIMAL_VALID)
        assert "childhood" in result.lower() or "portrait" in result.lower()

    def test_prompt_has_reasonable_length(self) -> None:
        result = build_prompt(MINIMAL_VALID)
        # Expect at least 200 characters and fewer than 3000
        assert 200 <= len(result) <= 3000

    def test_prompt_contains_newline_separator(self) -> None:
        """Prose and tag block should be separated by a blank line."""
        result = build_prompt(MINIMAL_VALID)
        assert "\n\n" in result

    def test_full_inputs_prompt_contains_features(self) -> None:
        result = build_prompt(FULL_VALID)
        assert "curly red hair" in result

    def test_full_inputs_prompt_contains_camera_style(self) -> None:
        result = build_prompt(FULL_VALID)
        assert "medium format film" in result

    def test_full_inputs_prompt_contains_gender(self) -> None:
        result = build_prompt(FULL_VALID)
        # gender is 'girl'
        assert "girl" in result.lower()

    def test_full_inputs_prompt_contains_age(self) -> None:
        result = build_prompt(FULL_VALID)
        assert "9" in result


# ---------------------------------------------------------------------------
# Tests: build_prompt — validation errors raised correctly
# ---------------------------------------------------------------------------


class TestBuildPromptValidationErrors:
    """Verify that build_prompt raises ValueError on bad inputs."""

    def test_raises_value_error_on_empty_inputs(self) -> None:
        with pytest.raises(ValueError):
            build_prompt({})

    def test_raises_value_error_on_invalid_decade(self) -> None:
        with pytest.raises(ValueError, match="Invalid inputs"):
            build_prompt(_make_inputs(decade="1850s"))

    def test_raises_value_error_on_invalid_mood(self) -> None:
        with pytest.raises(ValueError, match="Invalid inputs"):
            build_prompt(_make_inputs(mood="ecstatic"))

    def test_raises_value_error_on_invalid_preset(self) -> None:
        with pytest.raises(ValueError, match="Invalid inputs"):
            build_prompt(_make_inputs(preset_id="fake_preset"))

    def test_error_message_contains_bullet_points(self) -> None:
        try:
            build_prompt({})
        except ValueError as exc:
            assert "•" in str(exc)

    def test_raises_value_error_not_key_error(self) -> None:
        """Invalid preset_id must raise ValueError from build_prompt, not KeyError."""
        with pytest.raises(ValueError):
            build_prompt(_make_inputs(preset_id="does_not_exist"))


# ---------------------------------------------------------------------------
# Tests: build_prompt — all presets produce valid output
# ---------------------------------------------------------------------------


class TestBuildPromptAllPresets:
    """Ensure build_prompt works correctly for every available preset."""

    @pytest.mark.parametrize("preset", ALL_PRESETS, ids=[p["id"] for p in ALL_PRESETS])
    def test_each_preset_produces_non_empty_prompt(self, preset: dict) -> None:
        data = _make_inputs(preset_id=preset["id"])
        result = build_prompt(data)
        assert isinstance(result, str)
        assert len(result) > 100

    @pytest.mark.parametrize("preset", ALL_PRESETS, ids=[p["id"] for p in ALL_PRESETS])
    def test_each_preset_injects_film_stock_or_lens(self, preset: dict) -> None:
        data = _make_inputs(preset_id=preset["id"])
        result = build_prompt(data)
        # Either film stock name or lens description should appear
        film_stock = preset["film_stock"]
        lens_fragment = preset["lens"].split(",")[0]  # first part of lens description
        assert film_stock in result or lens_fragment in result, (
            f"Preset {preset['id']!r}: expected film stock or lens fragment in prompt"
        )

    @pytest.mark.parametrize("preset", ALL_PRESETS, ids=[p["id"] for p in ALL_PRESETS])
    def test_each_preset_label_appears_in_prompt(self, preset: dict) -> None:
        data = _make_inputs(preset_id=preset["id"])
        result = build_prompt(data)
        assert preset["label"] in result, (
            f"Preset label {preset['label']!r} not found in prompt"
        )

    @pytest.mark.parametrize("preset", ALL_PRESETS, ids=[p["id"] for p in ALL_PRESETS])
    def test_each_preset_injects_at_least_one_mood_modifier(self, preset: dict) -> None:
        data = _make_inputs(preset_id=preset["id"])
        result = build_prompt(data)
        found = any(modifier in result for modifier in preset["mood_modifiers"])
        assert found, (
            f"No mood modifier from {preset['mood_modifiers']} found in prompt for preset {preset['id']!r}"
        )

    @pytest.mark.parametrize("preset", ALL_PRESETS, ids=[p["id"] for p in ALL_PRESETS])
    def test_each_preset_injects_at_least_one_technical_tag(self, preset: dict) -> None:
        data = _make_inputs(preset_id=preset["id"])
        result = build_prompt(data)
        found = any(tag in result for tag in preset["technical_tags"])
        assert found, (
            f"No technical tag from {preset['technical_tags']} found in prompt for preset {preset['id']!r}"
        )


# ---------------------------------------------------------------------------
# Tests: build_prompt — all decades produce valid output
# ---------------------------------------------------------------------------


class TestBuildPromptAllDecades:
    """Ensure build_prompt works for every valid decade."""

    @pytest.mark.parametrize("decade", sorted(VALID_DECADES))
    def test_each_decade_produces_prompt_containing_decade(self, decade: str) -> None:
        data = _make_inputs(decade=decade)
        result = build_prompt(data)
        assert decade in result


# ---------------------------------------------------------------------------
# Tests: build_prompt — all moods produce valid output
# ---------------------------------------------------------------------------


class TestBuildPromptAllMoods:
    """Ensure build_prompt works for every valid mood."""

    @pytest.mark.parametrize("mood", sorted(VALID_MOODS))
    def test_each_mood_produces_non_empty_prompt(self, mood: str) -> None:
        data = _make_inputs(mood=mood)
        result = build_prompt(data)
        assert isinstance(result, str)
        assert len(result) > 100


# ---------------------------------------------------------------------------
# Tests: build_prompt — all genders produce valid output
# ---------------------------------------------------------------------------


class TestBuildPromptAllGenders:
    """Ensure build_prompt works for every valid gender value."""

    @pytest.mark.parametrize("gender", sorted(VALID_GENDERS))
    def test_each_gender_in_prompt(self, gender: str) -> None:
        data = _make_inputs(gender=gender)
        result = build_prompt(data)
        assert gender in result.lower()


# ---------------------------------------------------------------------------
# Tests: build_prompt — optional fields do not break output
# ---------------------------------------------------------------------------


class TestBuildPromptOptionalFields:
    """Verify optional fields enrich but do not break the prompt."""

    def test_no_features_still_produces_prompt(self) -> None:
        data = _make_inputs()  # no features key
        result = build_prompt(data)
        assert isinstance(result, str) and len(result) > 100

    def test_features_appears_in_prompt(self) -> None:
        data = _make_inputs(features="bright blue eyes and dimples")
        result = build_prompt(data)
        assert "bright blue eyes" in result

    def test_camera_style_appears_in_prompt(self) -> None:
        data = _make_inputs(camera_style="large format 4x5 camera")
        result = build_prompt(data)
        assert "large format 4x5" in result

    def test_age_string_in_prompt(self) -> None:
        data = _make_inputs(age="7")
        result = build_prompt(data)
        assert "7" in result

    def test_no_age_defaults_gracefully(self) -> None:
        data = _make_inputs()  # no age key
        result = build_prompt(data)
        # Should not crash; 'young' default may or may not be visible
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Tests: get_prompt_metadata
# ---------------------------------------------------------------------------


class TestGetPromptMetadata:
    """Tests for the get_prompt_metadata() helper."""

    def test_returns_dict(self) -> None:
        meta = get_prompt_metadata(MINIMAL_VALID)
        assert isinstance(meta, dict)

    def test_contains_preset_label(self) -> None:
        meta = get_prompt_metadata(MINIMAL_VALID)
        assert "preset_label" in meta
        assert meta["preset_label"] == "Warm Kodak Film"

    def test_contains_decade(self) -> None:
        meta = get_prompt_metadata(MINIMAL_VALID)
        assert meta["decade"] == "1980s"

    def test_contains_mood(self) -> None:
        meta = get_prompt_metadata(MINIMAL_VALID)
        assert meta["mood"] == "happy"

    def test_contains_char_count(self) -> None:
        meta = get_prompt_metadata(MINIMAL_VALID)
        assert "char_count" in meta
        assert isinstance(meta["char_count"], int)
        assert meta["char_count"] > 0

    def test_contains_word_count(self) -> None:
        meta = get_prompt_metadata(MINIMAL_VALID)
        assert "word_count" in meta
        assert isinstance(meta["word_count"], int)
        assert meta["word_count"] > 0

    def test_char_count_matches_actual_prompt(self) -> None:
        prompt = build_prompt(MINIMAL_VALID)
        meta = get_prompt_metadata(MINIMAL_VALID)
        assert meta["char_count"] == len(prompt)

    def test_word_count_approximately_correct(self) -> None:
        prompt = build_prompt(MINIMAL_VALID)
        meta = get_prompt_metadata(MINIMAL_VALID)
        assert meta["word_count"] == len(prompt.split())

    def test_raises_value_error_on_invalid_inputs(self) -> None:
        with pytest.raises(ValueError):
            get_prompt_metadata({})

    @pytest.mark.parametrize("preset", ALL_PRESETS, ids=[p["id"] for p in ALL_PRESETS])
    def test_preset_label_matches_preset_for_each_preset(self, preset: dict) -> None:
        data = _make_inputs(preset_id=preset["id"])
        meta = get_prompt_metadata(data)
        assert meta["preset_label"] == preset["label"]

    def test_full_inputs_metadata(self) -> None:
        meta = get_prompt_metadata(FULL_VALID)
        assert meta["decade"] == "1990s"
        assert meta["mood"] == "playful"
        assert meta["preset_label"] == "Golden Hour"
