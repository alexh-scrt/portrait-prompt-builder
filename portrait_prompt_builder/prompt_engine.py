"""Core prompt assembly engine for the Portrait Prompt Builder.

This module is responsible for combining structured user inputs with a
selected style preset to produce a single, polished, copy-ready prompt
string optimised for ChatGPT and Gemini image-generation models.

The assembly pipeline works in distinct stages:

1. **Validate** — ensure required fields are present and within allowed
   values; raise descriptive errors early so the Flask layer can return
   useful HTTP 400 responses.
2. **Normalise** — strip whitespace, title-case free-text fields where
   appropriate, and apply sensible defaults for optional inputs.
3. **Compose sections** — build discrete prose/tag sections (subject,
   setting, clothing, mood, camera/technical) from the normalised inputs
   and the preset's photographic vocabulary.
4. **Assemble** — join sections into a single coherent paragraph prompt
   followed by a comma-separated tag block, the way ChatGPT and Gemini
   respond best.

Public API
----------
- :func:`build_prompt` — primary entry-point used by the Flask routes.
- :func:`validate_inputs` — standalone validator; returns a list of
  human-readable error strings (empty list means valid).
- :func:`normalise_inputs` — returns a cleaned copy of the inputs dict.
- :data:`VALID_DECADES` — frozenset of accepted decade strings.
- :data:`VALID_MOODS` — frozenset of accepted mood strings.
"""

from __future__ import annotations

from typing import Any

from portrait_prompt_builder.presets import Preset, get_preset

# ---------------------------------------------------------------------------
# Constants — allowed field values
# ---------------------------------------------------------------------------

#: Accepted values for the ``decade`` field.
VALID_DECADES: frozenset[str] = frozenset(
    [
        "1950s",
        "1960s",
        "1970s",
        "1980s",
        "1990s",
        "2000s",
        "2010s",
    ]
)

#: Accepted values for the ``mood`` field.
VALID_MOODS: frozenset[str] = frozenset(
    [
        "happy",
        "curious",
        "dreamy",
        "melancholic",
        "playful",
        "serious",
        "adventurous",
        "shy",
    ]
)

#: Accepted values for the ``gender`` field (used in subject description).
VALID_GENDERS: frozenset[str] = frozenset(
    [
        "boy",
        "girl",
        "child",  # gender-neutral option
    ]
)

#: Required top-level keys that must be present and non-empty in *inputs*.
_REQUIRED_FIELDS: tuple[str, ...] = (
    "decade",
    "setting",
    "clothing",
    "mood",
    "preset_id",
)

# ---------------------------------------------------------------------------
# Decade → era adjective mapping (enriches the prompt with period flavour)
# ---------------------------------------------------------------------------

_DECADE_ERA_DESCRIPTORS: dict[str, str] = {
    "1950s": "post-war suburban America, pastel colour palettes, clean-cut style",
    "1960s": "cultural revolution, bold geometric patterns, mod fashion",
    "1970s": "earthy tones, wide lapels, wood-panelled interiors",
    "1980s": "neon accents, big hair, bold primary colours",
    "1990s": "grunge-inflected casual wear, muted plaids, windbreakers",
    "2000s": "early digital aesthetic, low-rise denim, graphic tees",
    "2010s": "Instagram-era filters, minimalist streetwear, smartphone selfie culture",
}

# ---------------------------------------------------------------------------
# Mood → expressive descriptor mapping
# ---------------------------------------------------------------------------

_MOOD_DESCRIPTORS: dict[str, str] = {
    "happy": "beaming smile, eyes full of joy, radiating warmth",
    "curious": "wide-eyed wonder, head slightly tilted, expression of deep curiosity",
    "dreamy": "faraway gaze, soft unfocused eyes, lost in thought",
    "melancholic": "wistful expression, gaze turned downward, quiet introspection",
    "playful": "mischievous grin, caught mid-laugh, carefree energy",
    "serious": "composed and thoughtful, direct gaze into the camera, composed posture",
    "adventurous": "confident stance, bright eyes, ready-for-anything expression",
    "shy": "slight blush, eyes glancing away, endearingly bashful",
}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_inputs(inputs: dict[str, Any]) -> list[str]:
    """Validate user inputs and return a list of human-readable error strings.

    An empty return value means the inputs are valid.  The Flask layer
    should call this before :func:`build_prompt` and return HTTP 400 with
    the error list if it is non-empty.

    Args:
        inputs: Raw dictionary of user-supplied form values.  Expected keys
            are documented in :func:`build_prompt`.

    Returns:
        A (possibly empty) list of human-readable validation error strings.

    Example::

        >>> errors = validate_inputs({})
        >>> "decade" in errors[0]
        True
    """
    errors: list[str] = []

    # ---- required fields ---------------------------------------------------
    for field in _REQUIRED_FIELDS:
        value = inputs.get(field, "")
        if not isinstance(value, str) or not value.strip():
            errors.append(f"'{field}' is required and must be a non-empty string.")

    # Bail early if basic presence checks already failed — further checks
    # would produce confusing secondary errors.
    if errors:
        return errors

    # ---- decade ------------------------------------------------------------
    decade = inputs["decade"].strip()
    if decade not in VALID_DECADES:
        errors.append(
            f"'{decade}' is not a valid decade. "
            f"Choose one of: {', '.join(sorted(VALID_DECADES))}."
        )

    # ---- mood --------------------------------------------------------------
    mood = inputs["mood"].strip().lower()
    if mood not in VALID_MOODS:
        errors.append(
            f"'{mood}' is not a valid mood. "
            f"Choose one of: {', '.join(sorted(VALID_MOODS))}."
        )

    # ---- gender (optional but must be valid when supplied) -----------------
    gender = inputs.get("gender", "").strip().lower()
    if gender and gender not in VALID_GENDERS:
        errors.append(
            f"'{gender}' is not a valid gender value. "
            f"Choose one of: {', '.join(sorted(VALID_GENDERS))} or leave blank."
        )

    # ---- preset_id ---------------------------------------------------------
    preset_id = inputs["preset_id"].strip()
    try:
        get_preset(preset_id)
    except KeyError:
        from portrait_prompt_builder.presets import PRESET_MAP  # local import

        errors.append(
            f"'{preset_id}' is not a valid preset id. "
            f"Choose one of: {', '.join(sorted(PRESET_MAP.keys()))}."
        )

    # ---- free-text length guards -------------------------------------------
    for field, max_len in [
        ("setting", 200),
        ("clothing", 200),
        ("features", 300),
        ("camera_style", 200),
    ]:
        value = inputs.get(field, "")
        if isinstance(value, str) and len(value) > max_len:
            errors.append(
                f"'{field}' must not exceed {max_len} characters "
                f"(got {len(value)})."
            )

    return errors


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------


def normalise_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    """Return a cleaned, normalised copy of the raw inputs dictionary.

    This function does **not** mutate *inputs*.  It strips whitespace from
    all string values, lower-cases enumerated fields, and applies defaults
    for optional fields.

    Args:
        inputs: Raw dictionary of user-supplied form values.

    Returns:
        A new dictionary containing normalised values ready for prompt
        assembly.

    Example::

        >>> norm = normalise_inputs({"decade": "  1980s  ", "mood": "HAPPY"})
        >>> norm["decade"]
        '1980s'
        >>> norm["mood"]
        'happy'
    """
    cleaned: dict[str, Any] = {}

    # String fields — strip whitespace universally
    string_fields = [
        "decade",
        "setting",
        "clothing",
        "mood",
        "gender",
        "features",
        "camera_style",
        "preset_id",
        "age",
    ]
    for field in string_fields:
        raw = inputs.get(field, "")
        cleaned[field] = str(raw).strip() if raw is not None else ""

    # Normalise enumerated / case-insensitive fields to lowercase
    for field in ("mood", "gender"):
        cleaned[field] = cleaned[field].lower()

    # Preserve original casing for free-text display fields but remove
    # leading/trailing whitespace (already done above).

    # Apply defaults for optional fields
    if not cleaned["gender"]:
        cleaned["gender"] = "child"

    if not cleaned["age"]:
        cleaned["age"] = "young"

    return cleaned


# ---------------------------------------------------------------------------
# Section builders (internal helpers)
# ---------------------------------------------------------------------------


def _build_subject_clause(
    normalised: dict[str, Any],
    preset: Preset,
) -> str:
    """Construct the subject/person description clause.

    Args:
        normalised: Normalised inputs dictionary.
        preset: The resolved style preset.

    Returns:
        A prose string describing the subject.
    """
    age_desc = normalised["age"]
    gender = normalised["gender"]

    # Map gender to natural language
    gender_noun = {
        "boy": "young boy",
        "girl": "young girl",
        "child": "young child",
    }.get(gender, "young child")

    # Prefix the age description if it's not already embedded
    subject_parts: list[str] = []

    # Age modifier
    if age_desc and age_desc.lower() not in ("young", ""):
        subject_parts.append(f"{age_desc}-year-old")

    subject_parts.append(gender_noun)

    # Optional ethnicity / physical features
    features = normalised.get("features", "").strip()
    if features:
        subject_parts.append(f"with {features}")

    return " ".join(subject_parts)


def _build_setting_clause(
    normalised: dict[str, Any],
    preset: Preset,
) -> str:
    """Construct the setting/environment clause.

    Args:
        normalised: Normalised inputs dictionary.
        preset: The resolved style preset.

    Returns:
        A prose phrase describing the scene location and era context.
    """
    setting = normalised["setting"]
    decade = normalised["decade"]
    era_detail = _DECADE_ERA_DESCRIPTORS.get(decade, "")

    parts = [setting]
    if era_detail:
        parts.append(f"evoking the aesthetic of {era_detail}")

    return ", ".join(parts)


def _build_clothing_clause(normalised: dict[str, Any]) -> str:
    """Construct the clothing/costume description clause.

    Args:
        normalised: Normalised inputs dictionary.

    Returns:
        A short prose phrase describing what the subject is wearing.
    """
    clothing = normalised["clothing"]
    decade = normalised["decade"]
    return f"dressed in {clothing}, typical of {decade} fashion"


def _build_mood_clause(normalised: dict[str, Any]) -> str:
    """Construct the emotional/mood description clause.

    Args:
        normalised: Normalised inputs dictionary.

    Returns:
        A prose phrase conveying the emotional tone of the portrait.
    """
    mood = normalised["mood"]
    mood_detail = _MOOD_DESCRIPTORS.get(mood, mood)
    return mood_detail


def _build_photography_clause(normalised: dict[str, Any], preset: Preset) -> str:
    """Construct the photography/technical description clause.

    Combines the preset's lens, lighting, film stock and colour-grade
    information with any user-supplied camera style preference.

    Args:
        normalised: Normalised inputs dictionary.
        preset: The resolved style preset.

    Returns:
        A prose string covering the technical photographic qualities.
    """
    parts: list[str] = []

    # Preset-driven technical details
    if preset.get("film_stock"):
        parts.append(f"shot on {preset['film_stock']}")

    parts.append(f"with {preset['lens']}")
    parts.append(preset["lighting"])
    parts.append(preset["colour_grade"])

    # User override / additional camera style
    camera_style = normalised.get("camera_style", "").strip()
    if camera_style:
        parts.append(camera_style)

    return ", ".join(parts)


def _build_style_tags(preset: Preset) -> str:
    """Produce a comma-separated tag string from preset modifiers.

    Args:
        preset: The resolved style preset.

    Returns:
        A comma-separated string of stylistic and technical tags.
    """
    tags: list[str] = []
    tags.extend(preset.get("mood_modifiers", []))
    tags.extend(preset.get("technical_tags", []))
    return ", ".join(tags)


# ---------------------------------------------------------------------------
# Primary public API
# ---------------------------------------------------------------------------


def build_prompt(inputs: dict[str, Any]) -> str:
    """Assemble a polished, copy-ready AI image-generation prompt.

    This is the primary public entry-point.  It validates, normalises, and
    then assembles a single coherent prompt string from the user's portrait
    details and the selected style preset.

    The resulting prompt is structured to work well with both ChatGPT
    (DALL-E) and Gemini Imagen image generation by combining a natural-
    language description paragraph with a comma-separated photographic tag
    block.

    Args:
        inputs: A dictionary of user-supplied form values.  The following
            keys are recognised:

            **Required:**

            - ``decade`` (str): The decade the portrait should evoke, e.g.
              ``"1980s"``.  Must be one of :data:`VALID_DECADES`.
            - ``setting`` (str): The scene location / environment, e.g.
              ``"suburban backyard with a wooden fence"``.
            - ``clothing`` (str): Description of clothing, e.g.
              ``"a striped polo shirt and corduroy trousers"``.
            - ``mood`` (str): The emotional tone of the subject, e.g.
              ``"happy"``.  Must be one of :data:`VALID_MOODS`.
            - ``preset_id`` (str): The id of the style preset to apply,
              e.g. ``"warm_kodak_film"``.

            **Optional:**

            - ``gender`` (str): ``"boy"``, ``"girl"``, or ``"child"``
              (default: ``"child"``).
            - ``age`` (str): Age or age description, e.g. ``"8"`` or
              ``"young"`` (default: ``"young"``).
            - ``features`` (str): Physical / ethnic features to include,
              e.g. ``"curly red hair and freckles"``.
            - ``camera_style`` (str): Additional camera or stylistic notes
              the user wants to inject verbatim.

    Returns:
        A fully assembled prompt string ready to paste into ChatGPT or
        Gemini.

    Raises:
        ValueError: If *inputs* fails validation.  The error message
            contains a newline-separated list of all validation failures so
            callers can surface them to the user.

    Example::

        >>> from portrait_prompt_builder.prompt_engine import build_prompt
        >>> prompt = build_prompt({
        ...     "decade": "1980s",
        ...     "setting": "a sunny suburban kitchen",
        ...     "clothing": "a striped polo shirt",
        ...     "mood": "happy",
        ...     "preset_id": "warm_kodak_film",
        ...     "gender": "boy",
        ...     "age": "8",
        ... })
        >>> isinstance(prompt, str)
        True
        >>> "1980s" in prompt
        True
    """
    # 1. Validate
    errors = validate_inputs(inputs)
    if errors:
        raise ValueError("Invalid inputs:\n" + "\n".join(f"  • {e}" for e in errors))

    # 2. Normalise
    norm = normalise_inputs(inputs)

    # 3. Resolve preset
    preset: Preset = get_preset(norm["preset_id"])

    # 4. Build clauses
    subject_clause = _build_subject_clause(norm, preset)
    setting_clause = _build_setting_clause(norm, preset)
    clothing_clause = _build_clothing_clause(norm)
    mood_clause = _build_mood_clause(norm)
    photography_clause = _build_photography_clause(norm, preset)
    style_tags = _build_style_tags(preset)

    # 5. Assemble prose paragraph
    #
    # Structure: "A portrait photograph of [SUBJECT], [MOOD EXPRESSION],
    # [CLOTHING], set in [SETTING]. [PHOTOGRAPHY DETAILS]. Style tags: ..."
    #
    # This structure is well-recognised by ChatGPT and Gemini and produces
    # consistent, high-quality results.
    decade = norm["decade"]
    preset_label = preset["label"]

    prose_lines: list[str] = [
        f"A childhood self-portrait photograph of {subject_clause}, "
        f"{mood_clause}, {clothing_clause}.",
        f"The scene is set in {setting_clause}.",
        f"Captured {photography_clause}.",
        f"The overall aesthetic is {preset_label} — "
        + ", ".join(preset["mood_modifiers"][:3])
        + ".",
    ]

    prose = "  ".join(prose_lines)

    # 6. Append comma-separated tag block (improves model adherence)
    tag_block_parts: list[str] = [
        f"{decade} era",
        "childhood portrait",
        "analog photography",
        style_tags,
        f"prompt optimised for ChatGPT and Gemini image generation",
    ]
    tag_block = ", ".join(part for part in tag_block_parts if part)

    # 7. Combine prose and tags
    final_prompt = f"{prose}\n\n{tag_block}"

    return final_prompt


def get_prompt_metadata(inputs: dict[str, Any]) -> dict[str, Any]:
    """Return metadata about a generated prompt without the full prompt text.

    Useful for the Flask layer to display summary information on the result
    page (e.g. the preset label, decade, and character count) alongside
    the full prompt.

    Args:
        inputs: Same dictionary accepted by :func:`build_prompt`.  Must
            pass validation.

    Returns:
        A dictionary with the following keys:

        - ``preset_label`` (str): Human-readable preset name.
        - ``decade`` (str): The chosen decade.
        - ``mood`` (str): The chosen mood.
        - ``char_count`` (int): Character length of the assembled prompt.
        - ``word_count`` (int): Approximate word count of the prompt.

    Raises:
        ValueError: Propagated from :func:`build_prompt` if inputs are
            invalid.

    Example::

        >>> meta = get_prompt_metadata({
        ...     "decade": "1990s",
        ...     "setting": "a school playground",
        ...     "clothing": "dungarees",
        ...     "mood": "playful",
        ...     "preset_id": "golden_hour",
        ... })
        >>> meta["decade"]
        '1990s'
    """
    prompt = build_prompt(inputs)  # raises ValueError if invalid
    norm = normalise_inputs(inputs)
    preset = get_preset(norm["preset_id"])

    return {
        "preset_label": preset["label"],
        "decade": norm["decade"],
        "mood": norm["mood"],
        "char_count": len(prompt),
        "word_count": len(prompt.split()),
    }


__all__ = [
    "VALID_DECADES",
    "VALID_MOODS",
    "VALID_GENDERS",
    "validate_inputs",
    "normalise_inputs",
    "build_prompt",
    "get_prompt_metadata",
]
