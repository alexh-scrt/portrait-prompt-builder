# Portrait Prompt Builder 📷

*Turn your childhood memories into stunning AI portraits — in seconds.*

---

## What It Does

Portrait Prompt Builder is a lightweight web app that guides you through a structured form to generate polished, copy-ready AI image prompts for the viral "childhood self portrait" trend. Fill in details like your decade, setting, clothing style, and mood, then pick from curated photographic style presets to produce a prompt optimized for ChatGPT or Gemini image generation. No account, no API keys, no database — just run it and go.

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/your-username/portrait_prompt_builder.git
cd portrait_prompt_builder

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
flask --app portrait_prompt_builder run

# 5. Open your browser
# Visit http://127.0.0.1:5000
```

That's it. Fill out the form, pick a style preset, and copy your prompt.

---

## Features

- **Guided multi-step form** — collects decade, setting, clothing, physical features, mood, and camera style in a clean, focused flow
- **5 curated style presets** — Black-and-White Cinematic, Warm Kodak Film, Golden Hour, Polaroid Instant, and Cool Studio Flash inject precise photographic language into every prompt
- **Smart prompt engine** — assembles your inputs and preset modifiers into a single coherent, detailed prompt tuned for ChatGPT and Gemini image generation
- **One-click copy & download** — copy the finished prompt to clipboard or save it as a `.txt` file for easy sharing on social media
- **Zero external dependencies at runtime** — no database, no third-party API calls; runs instantly as a local or hosted Flask app

---

## Usage Examples

### Running the development server

```bash
flask --app portrait_prompt_builder run --debug
```

### Running tests

```bash
pytest
```

### Example generated prompt

After submitting the form with the following inputs:

| Field         | Value                        |
|---------------|------------------------------|
| Decade        | 1990s                        |
| Setting       | backyard in summer           |
| Clothing      | oversized denim jacket       |
| Mood          | nostalgic                    |
| Style Preset  | Warm Kodak Film              |

The prompt engine produces something like:

```
A candid childhood portrait of a young girl in the 1990s, standing in a
sunlit backyard in summer, wearing an oversized denim jacket. The mood is
warm and nostalgic. Shot on Kodak Gold 200 film, slightly overexposed with
rich amber tones, soft grain, and natural bokeh. Photorealistic, cinematic
composition, shallow depth of field, golden afternoon light.
```

Paste directly into ChatGPT (`Imagine:`) or Gemini's image generation prompt box.

### Using the prompt engine programmatically

```python
from portrait_prompt_builder.prompt_engine import build_prompt
from portrait_prompt_builder.presets import WARM_KODAK_FILM

result = build_prompt(
    inputs={
        "decade": "1990s",
        "setting": "backyard in summer",
        "clothing": "oversized denim jacket",
        "mood": "nostalgic",
        "gender": "girl",
        "features": "freckles, brown hair",
    },
    preset=WARM_KODAK_FILM,
)

print(result["prompt"])
```

---

## Project Structure

```
portrait_prompt_builder/
├── pyproject.toml                        # Project metadata and build config
├── requirements.txt                      # Pinned pip dependencies
│
├── portrait_prompt_builder/
│   ├── __init__.py                       # Package init; exposes create_app factory
│   ├── app.py                            # Flask app factory and route definitions
│   ├── prompt_engine.py                  # Core prompt assembly logic
│   ├── presets.py                        # Style preset definitions
│   │
│   ├── templates/
│   │   ├── index.html                    # Multi-step guided form page
│   │   └── result.html                  # Generated prompt result page
│   │
│   └── static/
│       ├── style.css                     # Retro film-grain CSS styling
│       └── app.js                        # Multi-step form, clipboard, download JS
│
└── tests/
    ├── test_prompt_engine.py             # Unit tests for prompt assembly logic
    ├── test_routes.py                    # Flask integration tests for all routes
    └── test_presets.py                   # Unit tests for preset structure and helpers
```

---

## Configuration

The app uses environment variables for optional configuration. Create a `.env` file in the project root or set them in your shell:

| Variable        | Default       | Description                                              |
|-----------------|---------------|----------------------------------------------------------|
| `FLASK_ENV`     | `production`  | Set to `development` to enable debug mode and reloader  |
| `SECRET_KEY`    | Random bytes  | Flask session secret key — set explicitly in production  |
| `PORT`          | `5000`        | Port for the development server                          |

**Example `.env` for local development:**

```env
FLASK_ENV=development
SECRET_KEY=change-me-in-production
PORT=5000
```

> **Note:** The app has no database and makes no external API calls, so minimal configuration is needed to run it securely.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

*Built with [Jitter](https://github.com/jitter-ai) — an AI agent that ships code daily.*
