"""Unit tests for portrait_prompt_builder.presets module.

Covers preset structure validation, registry completeness, and the
helper function contracts defined in presets.py.
"""

from __future__ import annotations

import pytest

from portrait_prompt_builder.presets import (
    ALL_PRESETS,
    CINEMATIC_BW,
    GOLDEN_HOUR,
    POLAROID_INSTANT,
    PRESET_MAP,
    STUDIO_FLASH,
    WARM_KODAK_FILM,
    get_preset,
    list_presets,
    preset_choices,
)

# ---------------------------------------------------------------------------
# Expected preset ids
# ---------------------------------------------------------------------------

EXPECTED_IDS = {
    "cinematic_bw",
    "warm_kodak_film",
    "golden_hour",
    "polaroid_instant",
    "studio_flash",
}

REQUIRED_KEYS = {
    "id",
    "label",
    "description",
    "film_stock",
    "colour_grade",
    "lighting",
    "lens",
    "mood_modifiers",
    "technical_tags",
    "negative_tags",
}


# ---------------------------------------------------------------------------
# Tests: module-level constants
# ---------------------------------------------------------------------------


class TestAllPresets:
    """Tests for the ALL_PRESETS list and PRESET_MAP registry."""

    def test_all_presets_is_list(self) -> None:
        assert isinstance(ALL_PRESETS, list)

    def test_all_presets_has_five_entries(self) -> None:
        assert len(ALL_PRESETS) == 5

    def test_preset_map_is_dict(self) -> None:
        assert isinstance(PRESET_MAP, dict)

    def test_preset_map_has_all_expected_ids(self) -> None:
        assert set(PRESET_MAP.keys()) == EXPECTED_IDS

    def test_preset_map_values_are_dicts(self) -> None:
        for preset_id, preset in PRESET_MAP.items():
            assert isinstance(preset, dict), f"{preset_id} value is not a dict"

    def test_all_presets_and_map_are_consistent(self) -> None:
        """Every entry in ALL_PRESETS must appear in PRESET_MAP and vice versa."""
        list_ids = {p["id"] for p in ALL_PRESETS}
        assert list_ids == set(PRESET_MAP.keys())


# ---------------------------------------------------------------------------
# Tests: individual preset structure
# ---------------------------------------------------------------------------

\[email protected]("preset", ALL_PRESETS, ids=[p["id"] for p in ALL_PRESETS])
class TestPresetStructure:
    """Validates that every preset contains the required keys with correct types."""

    def test_has_all_required_keys(self, preset: dict) -> None:
        missing = REQUIRED_KEYS - set(preset.keys())
        assert not missing, f"Preset {preset['id']!r} missing keys: {missing}"

    def test_id_is_non_empty_string(self, preset: dict) -> None:
        assert isinstance(preset["id"], str)
        assert preset["id"].strip() != ""

    def test_label_is_non_empty_string(self, preset: dict) -> None:
        assert isinstance(preset["label"], str)
        assert preset["label"].strip() != ""

    def test_description_is_non_empty_string(self, preset: dict) -> None:
        assert isinstance(preset["description"], str)
        assert len(preset["description"]) > 10

    def test_lighting_is_non_empty_string(self, preset: dict) -> None:
        assert isinstance(preset["lighting"], str)
        assert preset["lighting"].strip() != ""

    def test_lens_is_non_empty_string(self, preset: dict) -> None:
        assert isinstance(preset["lens"], str)
        assert preset["lens"].strip() != ""

    def test_colour_grade_is_string(self, preset: dict) -> None:
        assert isinstance(preset["colour_grade"], str)

    def test_film_stock_is_string(self, preset: dict) -> None:
        # film_stock may be empty string for some presets
        assert isinstance(preset["film_stock"], str)

    def test_mood_modifiers_is_non_empty_list(self, preset: dict) -> None:
        assert isinstance(preset["mood_modifiers"], list)
        assert len(preset["mood_modifiers"]) >= 1
        for item in preset["mood_modifiers"]:
            assert isinstance(item, str) and item.strip() != ""

    def test_technical_tags_is_non_empty_list(self, preset: dict) -> None:
        assert isinstance(preset["technical_tags"], list)
        assert len(preset["technical_tags"]) >= 1
        for item in preset["technical_tags"]:
            assert isinstance(item, str) and item.strip() != ""

    def test_negative_tags_is_non_empty_list(self, preset: dict) -> None:
        assert isinstance(preset["negative_tags"], list)
        assert len(preset["negative_tags"]) >= 1
        for item in preset["negative_tags"]:
            assert isinstance(item, str) and item.strip() != ""

    def test_id_has_no_spaces(self, preset: dict) -> None:
        """IDs must be slug-like (underscores OK, spaces not)."""
        assert " " not in preset["id"]


# ---------------------------------------------------------------------------
# Tests: individual named presets
# ---------------------------------------------------------------------------


class TestNamedPresets:
    """Spot-check specific well-known preset values."""

    def test_cinematic_bw_id(self) -> None:
        assert CINEMATIC_BW["id"] == "cinematic_bw"

    def test_cinematic_bw_is_monochrome(self) -> None:
        colour_grade = CINEMATIC_BW["colour_grade"].lower()
        assert "monochrome" in colour_grade or "black" in colour_grade

    def test_warm_kodak_film_id(self) -> None:
        assert WARM_KODAK_FILM["id"] == "warm_kodak_film"

    def test_warm_kodak_film_mentions_kodak(self) -> None:
        assert "Kodak" in WARM_KODAK_FILM["film_stock"]

    def test_golden_hour_id(self) -> None:
        assert GOLDEN_HOUR["id"] == "golden_hour"

    def test_golden_hour_lighting_mentions_sunlight(self) -> None:
        lighting_lower = GOLDEN_HOUR["lighting"].lower()
        assert "golden" in lighting_lower or "sun" in lighting_lower

    def test_polaroid_instant_id(self) -> None:
        assert POLAROID_INSTANT["id"] == "polaroid_instant"

    def test_polaroid_mentions_polaroid_film_stock(self) -> None:
        assert "Polaroid" in POLAROID_INSTANT["film_stock"]

    def test_studio_flash_id(self) -> None:
        assert STUDIO_FLASH["id"] == "studio_flash"

    def test_studio_flash_lighting_mentions_strobe_or_flash(self) -> None:
        lighting_lower = STUDIO_FLASH["lighting"].lower()
        assert "strobe" in lighting_lower or "flash" in lighting_lower or "softbox" in lighting_lower


# ---------------------------------------------------------------------------
# Tests: get_preset helper
# ---------------------------------------------------------------------------


class TestGetPreset:
    """Tests for the get_preset() helper function."""

    def test_returns_correct_preset_for_each_id(self) -> None:
        for preset_id in EXPECTED_IDS:
            preset = get_preset(preset_id)
            assert preset["id"] == preset_id

    def test_returns_dict(self) -> None:
        preset = get_preset("cinematic_bw")
        assert isinstance(preset, dict)

    def test_raises_key_error_for_unknown_id(self) -> None:
        with pytest.raises(KeyError, match="unknown_preset"):
            get_preset("unknown_preset")

    def test_error_message_lists_available_presets(self) -> None:
        with pytest.raises(KeyError) as exc_info:
            get_preset("does_not_exist")
        error_str = str(exc_info.value)
        # At least one valid id should appear in the error message
        assert "cinematic_bw" in error_str or "Available" in error_str

    def test_case_sensitive_id_lookup(self) -> None:
        """IDs are case-sensitive; uppercase variant must raise KeyError."""
        with pytest.raises(KeyError):
            get_preset("CINEMATIC_BW")


# ---------------------------------------------------------------------------
# Tests: list_presets helper
# ---------------------------------------------------------------------------


class TestListPresets:
    """Tests for the list_presets() helper function."""

    def test_returns_list(self) -> None:
        result = list_presets()
        assert isinstance(result, list)

    def test_returns_five_presets(self) -> None:
        result = list_presets()
        assert len(result) == 5

    def test_returns_copy_not_same_object(self) -> None:
        result = list_presets()
        assert result is not ALL_PRESETS

    def test_mutating_result_does_not_affect_all_presets(self) -> None:
        result = list_presets()
        original_len = len(ALL_PRESETS)
        result.append({"id": "fake"})
        assert len(ALL_PRESETS) == original_len

    def test_order_matches_all_presets(self) -> None:
        result = list_presets()
        for idx, preset in enumerate(result):
            assert preset["id"] == ALL_PRESETS[idx]["id"]


# ---------------------------------------------------------------------------
# Tests: preset_choices helper
# ---------------------------------------------------------------------------


class TestPresetChoices:
    """Tests for the preset_choices() helper function."""

    def test_returns_list(self) -> None:
        choices = preset_choices()
        assert isinstance(choices, list)

    def test_returns_five_choices(self) -> None:
        choices = preset_choices()
        assert len(choices) == 5

    def test_each_choice_is_two_tuple(self) -> None:
        for choice in preset_choices():
            assert isinstance(choice, tuple)
            assert len(choice) == 2

    def test_first_element_is_id_string(self) -> None:
        for preset_id, label in preset_choices():
            assert isinstance(preset_id, str)
            assert preset_id in EXPECTED_IDS

    def test_second_element_is_label_string(self) -> None:
        for preset_id, label in preset_choices():
            assert isinstance(label, str)
            assert label.strip() != ""

    def test_first_choice_is_cinematic_bw(self) -> None:
        choices = preset_choices()
        assert choices[0] == ("cinematic_bw", "Black-and-White Cinematic")

    def test_labels_match_preset_labels(self) -> None:
        """Verify (id, label) pairs exactly mirror the source presets."""
        for preset_id, label in preset_choices():
            assert get_preset(preset_id)["label"] == label
