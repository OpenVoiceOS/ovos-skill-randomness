"""Every locale intent template must be valid under OVOS-INTENT-1.

A malformed line (for example two slots separated only by whitespace) is
silently skipped at load time, so the phrasing never matches. Assert instead
that every template line in every locale expands without error.
"""
from pathlib import Path

import pytest
from ovos_spec_tools.expansion import expand

LOCALE_DIR = Path(__file__).resolve().parent.parent / "skill_randomness" / "locale"


def _template_lines():
    for intent in sorted(LOCALE_DIR.glob("*/intents/*.intent")):
        for lineno, raw in enumerate(intent.read_text(encoding="utf-8").splitlines(), 1):
            line = raw.strip()
            if line and not line.startswith("#"):
                yield intent, lineno, line


TEMPLATES = list(_template_lines())


@pytest.mark.parametrize(
    "intent,lineno,line",
    TEMPLATES,
    ids=[f"{p.parent.parent.name}/{p.name}:{n}" for p, n, _ in TEMPLATES],
)
def test_template_expands(intent, lineno, line):
    samples = expand(line)
    assert samples, f"{intent}:{lineno} expanded to nothing"
