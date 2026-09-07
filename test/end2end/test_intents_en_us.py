"""End-to-end intent routing tests for the en-US locale.

Each canonical utterance is fired through a real MiniCroft and asserted to
route to the expected Padatious intent handler. The responses are random, so
assertions cover the intent binding only, not the spoken content.
"""
import unittest

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovoscope import CaptureSession, get_minicroft

SKILL_ID = "skill-ovos-randomness.openvoiceos"
LANG = "en-US"


class TestRandomnessIntentsEnUS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.minicroft = get_minicroft([SKILL_ID])

    @classmethod
    def tearDownClass(cls):
        cls.minicroft.stop()

    def _assert_intent(self, text, intent_file):
        # Some handlers follow up with get_response, which blocks on a reply that
        # never arrives; end the capture as soon as the intent is matched so the
        # assertion covers routing without waiting on the conversational tail.
        #
        # The padatious pipeline plugin emits the matched-intent message type
        # without the ".intent" file extension (e.g. "skill:pick-a-number",
        # not "skill:pick-a-number.intent"); strip it here so the fixture
        # tracks that naming instead of the on-disk intent filename.
        intent_msg = f"{SKILL_ID}:{intent_file.removesuffix('.intent')}"
        session = Session("test-session")
        session.lang = LANG
        session.pipeline = [
            "ovos-padatious-pipeline-plugin-high",
            "ovos-padatious-pipeline-plugin-medium",
        ]
        utterance = Message(
            "recognizer_loop:utterance",
            {"utterances": [text], "lang": LANG},
            {"session": session.serialize(), "source": "A", "destination": "B"},
        )
        capture = CaptureSession(self.minicroft, eof_msgs=[intent_msg])
        capture.capture(utterance, timeout=30)
        types = [m.msg_type for m in capture.finish()]
        self.assertIn(intent_msg, types)

    def test_choose_a_number_between_one_and_one_hundred(self):
        self._assert_intent("choose a number between one and one hundred", "pick_a_number.intent")

    def test_pick_a_number_between_20_and_21(self):
        self._assert_intent("pick a number between 20 and 21", "pick_a_number.intent")

    def test_flip_a_coin(self):
        self._assert_intent("flip a coin", "flip_a_coin.intent")

    def test_roll_a_20_sided_die(self):
        self._assert_intent("roll a 20 sided die", "roll_single_die.intent")

    def test_roll_a_die(self):
        self._assert_intent("roll a die", "roll_single_die.intent")
