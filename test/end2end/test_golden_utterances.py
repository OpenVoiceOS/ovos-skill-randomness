"""Golden-utterance end-to-end coverage for ovos-skill-randomness (en-US).

The golden corpus (``golden_utterances.jsonl``) is a vendored slice of the
shared ovoscope golden-utterance dataset, keyed by
``skill_id == "ovos-skill-randomness.openvoiceos"``. One shared ``MiniCroft``
is booted for the whole module and every row is driven through it, asserting
the expected Padatious intent binding via ``ovos.intent.matched``.

Two real findings came out of building this suite:

1. ``skill_randomness/locale/en-US/intents/roll-multiple-dice.intent`` had a
   sample with two adjacent slots and no literal word between them
   (``roll {number} {faces} sided (dice|die)``), rejected outright by the
   ``ovos_spec_tools`` template validator (``MalformedTemplate: adjacent
   slots ... a literal word must separate any two slots``) whenever it is
   the resolved version. This PR adds a literal ``of`` separator to make the
   sample well-formed. The exact golden phrasing without a separator
   (``"roll 6 20 sided die"``) is structurally unrecoverable — padatious
   cannot resolve the boundary between two bare numeric slots — but is
   still exercised below rather than dropped, since it now correctly
   resolves via the ``roll {number} d {faces}``/``roll {number} (dice|die)``
   samples' training succeeding (the failure mode was training-time, not
   phrasing-time).
2. ``make-a-choice.intent`` and ``fortune-teller.intent`` both call
   ``self.get_response()``. On ovoscope's synchronous FakeBus that blocks
   the emitting thread forever when nothing answers the follow-up prompt —
   the existing hand-written ``test_intents_en_us.py`` silently omits both
   intents for the same reason. Capture below runs in a daemon thread with
   a hard join timeout so the hang degrades to a clean, reported "TIMEOUT"
   instead of wedging the test run, and the corresponding golden rows are
   marked ``xfail(strict=True)`` with that exact reason.
"""
import json
import threading
from pathlib import Path

import pytest
from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovoscope import CaptureSession, get_minicroft

SKILL_ID = "skill-ovos-randomness.openvoiceos"
LANG = "en-US"

_PIPELINE = [
    "ovos-padatious-pipeline-plugin-high",
    "ovos-padatious-pipeline-plugin-medium",
]

GOLDEN_PATH = Path(__file__).parent / "golden_utterances.jsonl"

# intents whose handler calls self.get_response(): ovoscope's synchronous
# FakeBus blocks the emitting thread forever when nothing answers the
# follow-up prompt (see module docstring point 2).
_GET_RESPONSE_INTENTS = {"make-a-choice.intent", "fortune-teller.intent"}
_GET_RESPONSE_REASON = (
    "coverage gap: make-a-choice.intent/fortune-teller.intent call "
    "self.get_response(), which blocks the emitting thread forever on "
    "ovoscope's synchronous FakeBus when nothing answers the follow-up "
    "prompt (existing test_intents_en_us.py omits both intents for the "
    "same reason). See module docstring for full evidence."
)

# utterances lifted verbatim from OTHER skills' golden-utterance slices,
# picked for lexical overlap with this skill's "random"/"number" vocabulary.
NEGATIVE_UTTERANCES = [
    ("curiosity number", "ovos-skill-number-facts.openvoiceos"),
    ("curiosity number aleatory", "ovos-skill-number-facts.openvoiceos"),
    ("display random wiki", "ovos-skill-wikipedia.openvoiceos"),
    ("display random wikipedia", "ovos-skill-wikipedia.openvoiceos"),
    ("open random wiki", "ovos-skill-wikipedia.openvoiceos"),
    ("open random wikipedia", "ovos-skill-wikipedia.openvoiceos"),
]


def _load_golden_rows():
    rows = []
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("needs_manual"):
                continue
            rows.append(row)
    return rows


GOLDEN_ROWS = _load_golden_rows()


def _golden_id(row):
    return row["utterance"]


def _golden_param(row):
    marks = []
    if row["intent_label"] in _GET_RESPONSE_INTENTS:
        marks.append(pytest.mark.xfail(reason=_GET_RESPONSE_REASON, strict=True))
    return pytest.param(row, id=_golden_id(row), marks=marks)


GOLDEN_PARAMS = [_golden_param(row) for row in GOLDEN_ROWS]


@pytest.fixture(scope="module")
def minicroft():
    mc = get_minicroft([SKILL_ID])
    yield mc
    mc.stop()


def _capture_worker(mc, text, session_id, intent_msg, result):
    session = Session(session_id)
    session.lang = LANG
    session.pipeline = list(_PIPELINE)
    session.blacklisted_intents = []
    utterance = Message(
        "recognizer_loop:utterance",
        {"utterances": [text], "lang": LANG},
        {"session": session.serialize(), "source": "A", "destination": "B"},
    )
    capture = CaptureSession(mc, eof_msgs=[intent_msg])
    capture.capture(utterance, timeout=15)
    result["messages"] = capture.finish()
    result["done"] = True


def _capture(mc, text, session_id, intent_msg, hard_timeout=20):
    """Capture with a hard thread-join timeout; see module docstring point 2."""
    result = {"done": False, "messages": []}
    t = threading.Thread(
        target=_capture_worker,
        args=(mc, text, session_id, intent_msg, result),
        daemon=True,
    )
    t.start()
    t.join(hard_timeout)
    return result["messages"] if result["done"] else None


def _matched_intent_name(messages):
    if messages is None:
        return "TIMEOUT"
    for message in messages:
        if message.msg_type == "ovos.intent.matched":
            return message.data.get("intent_name")
    return None


@pytest.mark.parametrize("row", GOLDEN_PARAMS)
def test_golden_utterance(minicroft, row):
    base = row["intent_label"].removesuffix(".intent")
    expected = f"{SKILL_ID}:{base}"
    messages = _capture(minicroft, row["utterance"], f"golden-{_golden_id(row)}", expected)
    got = _matched_intent_name(messages)
    assert got == expected, f"{row['utterance']!r}: expected {expected!r}, got {got!r}"


@pytest.mark.parametrize("negative", NEGATIVE_UTTERANCES, ids=lambda n: n[0])
def test_negative_confusable_not_claimed(minicroft, negative):
    text, source_skill = negative
    messages = _capture(minicroft, text, f"negative-{text}", "ovos.intent.matched")
    claimed = bool(messages) and any(
        m.msg_type.startswith(f"{SKILL_ID}:") for m in messages
    )
    assert not claimed, f"{text!r} (from {source_skill}) was incorrectly claimed by {SKILL_ID}"
