"""Style presets for the Portrait Prompt Builder.

This module defines all curated photographic style presets as structured
data dictionaries.  Each preset encapsulates a distinct aesthetic that
can be applied to user portrait inputs to produce evocative, technically
precise AI image-generation prompts.

Preset structure
----------------
Each preset is a :class:`dict` with the following keys:

``id`` : str
    A short machine-readable identifier used in form values and URL
    parameters.
``label`` : str
    Human-readable display name shown in the UI.
``description`` : str
    Short marketing-style blurb that helps users choose the right look.
``film_stock`` : str
    Film stock or sensor description injected into the prompt to anchor
    the colour science of the image (e.g. ``"Kodak Portra 400"`` or
    ``"Ilford HP5 Plus"``).  Empty string when not applicable.
``colour_grade`` : str
    Short phrase describing the colour treatment or toning of the image.
``lighting`` : str
    Lighting descriptor that sets the mood (e.g. ``"soft window light"``,
    ``"hard noon sunlight"``).  Injected into the prompt's lighting
    section.
``lens`` : str
    Lens/optics description including focal length and rendering
    characteristics.
``mood_modifiers`` : list[str]
    Additional adjectives / stylistic tags that reinforce the preset's
    aesthetic identity.
``technical_tags`` : list[str]
    Low-level photographic or post-processing tags (e.g.
    ``"grain texture"``, ``"vignette"``).  Appended near the end of the
    assembled prompt.
``negative_tags`` : list[str]
    Tags hinting at elements to *avoid*, surfaced as negative-prompt
    guidance when the downstream model supports it (ChatGPT / Gemini).
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------

Preset = dict[str, Any]

# ---------------------------------------------------------------------------
# Individual preset definitions
# ---------------------------------------------------------------------------

#: Cinematic black-and-white preset inspired by mid-century portrait masters.
CINEMATIC_BW: Preset = {
    "id": "cinematic_bw",
    "label": "Black-and-White Cinematic",
    "description": (
        "Timeless monochrome with deep contrast and rich tonal range, "
        "reminiscent of 1950s–1970s film photography."
    ),
    "film_stock": "Ilford HP5 Plus 400",
    "colour_grade": "high-contrast monochrome, deep blacks, bright highlights",
    "lighting": "dramatic Rembrandt lighting with soft shadow falloff",
    "lens": "85mm f/1.4 portrait lens, shallow depth of field, creamy bokeh",
    "mood_modifiers": [
        "timeless",
        "emotive",
        "cinematic",
        "contemplative",
        "editorial",
    ],
    "technical_tags": [
        "fine grain texture",
        "rich tonal gradation",
        "slight vignette",
        "analog film look",
        "silver gelatin print aesthetic",
    ],
    "negative_tags": [
        "colour",
        "oversaturated",
        "digital plastic look",
        "HDR",
        "flat tones",
    ],
}

#: Warm Kodak film preset evoking 1970s–1990s consumer photography nostalgia.
WARM_KODAK_FILM: Preset = {
    "id": "warm_kodak_film",
    "label": "Warm Kodak Film",
    "description": (
        "Nostalgic warm tones and soft grain that feel like a beloved "
        "family photograph from the 1980s or early 1990s."
    ),
    "film_stock": "Kodak Portra 400",
    "colour_grade": "warm amber-orange tones, lifted shadows, faded highlights",
    "lighting": "soft diffused natural light, slight warm colour cast",
    "lens": "50mm f/2.0 standard lens, natural perspective, gentle bokeh",
    "mood_modifiers": [
        "nostalgic",
        "warm",
        "intimate",
        "candid",
        "heartfelt",
    ],
    "technical_tags": [
        "medium film grain",
        "warm colour cast",
        "slightly faded look",
        "analog halation",
        "authentic snapshot feel",
    ],
    "negative_tags": [
        "cold tones",
        "harsh shadows",
        "clinical sharpness",
        "digital noise",
        "over-edited",
    ],
}

#: Golden-hour preset capturing the magic of late-afternoon sunlight.
GOLDEN_HOUR: Preset = {
    "id": "golden_hour",
    "label": "Golden Hour",
    "description": (
        "Bathed in the warm, low-angle glow of late-afternoon sunlight with "
        "long soft shadows and luminous skin tones."
    ),
    "film_stock": "Kodak Ektar 100",
    "colour_grade": "rich golden-yellow palette, warm skin tones, glowing highlights",
    "lighting": (
        "golden-hour sunlight at low angle, strong rim lighting, "
        "long soft shadows"
    ),
    "lens": "35mm f/2.0 wide-angle lens, sunflare, natural perspective",
    "mood_modifiers": [
        "radiant",
        "dreamy",
        "magical",
        "sun-kissed",
        "euphoric",
    ],
    "technical_tags": [
        "lens flare",
        "golden light wrap",
        "warm bokeh",
        "high dynamic range tones",
        "luminous exposure",
    ],
    "negative_tags": [
        "flat lighting",
        "cold blue tones",
        "overcast sky",
        "artificial lighting",
        "desaturated",
    ],
}

#: Polaroid instant-film preset with its distinctive square format and quirks.
POLAROID_INSTANT: Preset = {
    "id": "polaroid_instant",
    "label": "Polaroid Instant",
    "description": (
        "Iconic instant-film look with faded edges, slight colour shifts, "
        "and the unmistakable warmth of a physical Polaroid print."
    ),
    "film_stock": "Polaroid 600 instant film",
    "colour_grade": (
        "muted, slightly faded colours with greenish shadow tint and "
        "warm highlight bleed"
    ),
    "lighting": "on-camera flash or bright ambient indoor light",
    "lens": "106mm f/14.6 fixed lens, slight soft-focus, limited sharpness",
    "mood_modifiers": [
        "quirky",
        "lo-fi",
        "charming",
        "spontaneous",
        "memory-like",
    ],
    "technical_tags": [
        "square crop",
        "faded edge vignette",
        "chemical colour shift",
        "light leaks",
        "low contrast",
        "soft focus",
    ],
    "negative_tags": [
        "sharp details",
        "high contrast",
        "clean colours",
        "professional lighting",
        "digital precision",
    ],
}

#: Cool studio flash preset with clean, modern editorial styling.
STUDIO_FLASH: Preset = {
    "id": "studio_flash",
    "label": "Cool Studio Flash",
    "description": (
        "Crisp, clean studio portrait with cool-toned strobe lighting "
        "against a seamless backdrop — sharp, modern, and editorial."
    ),
    "film_stock": "Fujifilm Velvia 50",
    "colour_grade": "neutral-to-cool colour balance, clean whites, precise exposure",
    "lighting": (
        "large softbox key light, fill reflector, cool-toned strobe flash, "
        "seamless white or grey backdrop"
    ),
    "lens": "90mm f/5.6 macro-portrait lens, tack-sharp focus, minimal distortion",
    "mood_modifiers": [
        "polished",
        "confident",
        "editorial",
        "crisp",
        "contemporary",
    ],
    "technical_tags": [
        "high resolution",
        "studio strobe",
        "catch-lights in eyes",
        "shadow-free background",
        "precise skin rendering",
    ],
    "negative_tags": [
        "warm tones",
        "grain",
        "outdoor setting",
        "blurred background",
        "lo-fi aesthetic",
    ],
}

# ---------------------------------------------------------------------------
# Master registry
# ---------------------------------------------------------------------------

#: Ordered list of all available presets.
ALL_PRESETS: list[Preset] = [
    CINEMATIC_BW,
    WARM_KODAK_FILM,
    GOLDEN_HOUR,
    POLAROID_INSTANT,
    STUDIO_FLASH,
]

#: Mapping from preset ``id`` to preset dict for O(1) look-up.
PRESET_MAP: dict[str, Preset] = {preset["id"]: preset for preset in ALL_PRESETS}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def get_preset(preset_id: str) -> Preset:
    """Retrieve a preset by its unique identifier.

    Args:
        preset_id: The ``id`` field of the desired preset (e.g.
            ``"cinematic_bw"`` or ``"golden_hour"``).

    Returns:
        The matching preset dictionary.

    Raises:
        KeyError: If no preset with the given *preset_id* exists.

    Example::

        >>> from portrait_prompt_builder.presets import get_preset
        >>> preset = get_preset("warm_kodak_film")
        >>> preset["label"]
        'Warm Kodak Film'
    """
    if preset_id not in PRESET_MAP:
        available = ", ".join(sorted(PRESET_MAP.keys()))
        raise KeyError(
            f"Unknown preset id {preset_id!r}. "
            f"Available presets: {available}"
        )
    return PRESET_MAP[preset_id]


def list_presets() -> list[Preset]:
    """Return a shallow copy of the ordered preset list.

    Returning a copy prevents callers from accidentally mutating the
    module-level ``ALL_PRESETS`` list.

    Returns:
        List of all preset dicts in display order.

    Example::

        >>> from portrait_prompt_builder.presets import list_presets
        >>> presets = list_presets()
        >>> [p["id"] for p in presets]
        ['cinematic_bw', 'warm_kodak_film', 'golden_hour', 'polaroid_instant', 'studio_flash']
    """
    return list(ALL_PRESETS)


def preset_choices() -> list[tuple[str, str]]:
    """Return a list of ``(id, label)`` tuples suitable for HTML select elements.

    Returns:
        Ordered list of ``(preset_id, human_label)`` pairs.

    Example::

        >>> from portrait_prompt_builder.presets import preset_choices
        >>> choices = preset_choices()
        >>> choices[0]
        ('cinematic_bw', 'Black-and-White Cinematic')
    """
    return [(preset["id"], preset["label"]) for preset in ALL_PRESETS]


__all__ = [
    "Preset",
    "CINEMATIC_BW",
    "WARM_KODAK_FILM",
    "GOLDEN_HOUR",
    "POLAROID_INSTANT",
    "STUDIO_FLASH",
    "ALL_PRESETS",
    "PRESET_MAP",
    "get_preset",
    "list_presets",
    "preset_choices",
]
