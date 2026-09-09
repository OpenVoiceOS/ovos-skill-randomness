"""Every locale resource must carry a name the skill actually looks up.

A locale file whose basename does not match the name in ``@intent_handler``
or ``speak_dialog`` is never found: the intent silently fails to register and
the dialog silently falls back to en-US, so the locale looks translated while
the user hears English.
"""
import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent / "skill_randomness"
LOCALE_DIR = SKILL_DIR / "locale"
SOURCE = (SKILL_DIR / "__init__.py").read_text(encoding="utf-8")

REGISTERED_INTENTS = set(re.findall(r'@intent_handler\("([^"]+)"\)', SOURCE))
SPOKEN_DIALOGS = {f"{name}.dialog"
                  for name in re.findall(r'speak_dialog\(\s*"([^"]+)"', SOURCE)}


def test_the_source_registers_the_names_this_test_checks():
    assert REGISTERED_INTENTS, "no @intent_handler found; the regex is stale"
    assert SPOKEN_DIALOGS, "no speak_dialog found; the regex is stale"


def test_every_shipped_intent_file_is_registered():
    orphans = sorted(str(p.relative_to(LOCALE_DIR))
                     for p in LOCALE_DIR.glob("*/intents/*.intent")
                     if p.name not in REGISTERED_INTENTS)
    assert orphans == [], "no @intent_handler names these files"


def test_every_shipped_dialog_file_is_spoken():
    known = SPOKEN_DIALOGS | {p.name for p in (LOCALE_DIR / "en-US" / "dialog").glob("*.dialog")}
    orphans = sorted(str(p.relative_to(LOCALE_DIR))
                     for p in LOCALE_DIR.glob("*/dialog/*.dialog")
                     if p.name not in known)
    assert orphans == [], "these dialog names exist in no other locale and are spoken nowhere"
