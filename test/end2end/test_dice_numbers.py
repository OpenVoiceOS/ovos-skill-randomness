"""End-to-end checks that the dice handlers read the number slots.

randint is patched to return its upper bound, so the spoken result names the
number of faces and the spoken total shows the number of dice.
"""
import re
import unittest
from unittest.mock import patch

from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from ovoscope import CaptureSession, get_minicroft

SKILL_ID = "skill-ovos-randomness.openvoiceos"

# (lang, utterance, faces, dice)
CASES = [
    ("en-US", "roll a 20 sided die", 20, 1),
    ("en-US", "roll a twelve sided die", 12, 1),
    ("en-US", "roll twelve dice", 6, 12),
    ("fr-FR", "lance un dé à 20 faces", 20, 1),
    ("fr-FR", "lance un dé à douze faces", 12, 1),
    ("fr-FR", "lance douze dés", 6, 12),
    ("da-DK", "kast en terning med 20 sider", 20, 1),
    ("da-DK", "kast en terning med tolv sider", 12, 1),
    ("da-DK", "kast tolv terninger", 6, 12),
]


class TestDiceNumbers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.minicroft = get_minicroft([SKILL_ID], secondary_langs=["fr-FR", "da-DK"])

    @classmethod
    def tearDownClass(cls):
        cls.minicroft.stop()

    def _spoken(self, lang, text):
        session = Session("test-session")
        session.lang = lang
        session.pipeline = [
            "ovos-padatious-pipeline-plugin-high",
            "ovos-padatious-pipeline-plugin-medium",
        ]
        utterance = Message(
            "recognizer_loop:utterance",
            {"utterances": [text], "lang": lang},
            {"session": session.serialize(), "source": "A", "destination": "B"},
        )
        capture = CaptureSession(self.minicroft, eof_msgs=["ovos.utterance.handled"])
        with patch("skill_randomness.randint", side_effect=lambda a, b: b):
            capture.capture(utterance, timeout=30)
        return [m.data["utterance"] for m in capture.finish()
                if m.msg_type == "ovos.utterance.speak"]

    def test_spoken_dice_result(self):
        for lang, text, faces, dice in CASES:
            with self.subTest(lang=lang, text=text):
                spoken = self._spoken(lang, text)
                self.assertEqual(len(spoken), 1, spoken)
                numbers = [int(n) for n in re.findall(r"\d+", spoken[0])]
                if dice == 1:
                    self.assertEqual(numbers, [faces], spoken)
                else:
                    self.assertEqual(numbers, [faces] * dice + [faces * dice], spoken)
