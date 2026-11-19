"""The number and the faces of dice are read in every locale that has a numtag lexicon.

Each row is a phrase of the locale's own roll_*.intent. padacioso cuts the
slots out of the phrase; the handler must roll the dice a speaker asks for.
The gold is the numbers in the phrase, not a parser result.
"""
from os.path import dirname, join
from unittest.mock import Mock, PropertyMock, patch

import pytest
from ovos_bus_client.message import Message
from padacioso import IntentContainer

from skill_randomness import RandomnessSkill

LOCALE = join(dirname(dirname(__file__)), "skill_randomness", "locale")

# (locale dir, skill lang, utterance, number of dice, faces)
MULTIPLE = [
    ("da-DK", "da-dk", "kast tre terninger med seks sider", 3, 6),
    ("da-DK", "da-dk", "kast fire terninger med tyve sider", 4, 20),
    ("en-US", "en-us", "roll three of six sided dice", 3, 6),
    ("en-US", "en-us", "roll four of twenty sided dice", 4, 20),
    ("en-US", "en-us", "roll 2 of 8 sided dice", 2, 8),
    ("eu-ES", "eu-es", "bota hiru d sei", 3, 6),
    ("fr-FR", "fr-fr", "lance trois dés à six faces", 3, 6),
    ("fr-FR", "fr-fr", "lance quatre dés à vingt faces", 4, 20),
    ("gl-ES", "gl-es", "lanza tres dados de seis caras", 3, 6),
    ("gl-ES", "gl-es", "lanza catro dados de vinte caras", 4, 20),
    ("kab", "kab", "deqqeṛ kraḍ d sḍis", 3, 6),
    ("sv-SE", "sv-se", "kasta tre tärningar med sex sidor", 3, 6),
    ("sv-SE", "sv-se", "kasta fyra tärningar med tjugo sidor", 4, 20),
]

# two numbers in the slot: the first one is the number of dice
TWO_NUMBERS = [
    ("en-US", "en-us", "roll two or three dice", 2),
    ("fr-FR", "fr-fr", "lance deux ou trois dés", 2),
]

# (locale dir, skill lang, utterance, faces)
SINGLE = [
    ("da-DK", "da-dk", "kast en terning med tyve sider", 20),
    ("en-US", "en-us", "roll a twenty sided die", 20),
    ("en-US", "en-us", "roll a 12 sided die", 12),
    ("eu-ES", "eu-es", "bota hogei aldeko dadoa", 20),
    ("fr-FR", "fr-fr", "lance un dé à vingt faces", 20),
    ("gl-ES", "gl-es", "lanza dados de vinte caras", 20),
    ("sv-SE", "sv-se", "kasta en tärning med tjugo sidor", 20),
]


def _slots(locale, intent, utterance):
    with open(join(LOCALE, locale, "intents", f"{intent}.intent"), encoding="utf-8") as f:
        container = IntentContainer()
        container.add_intent(intent, f.read().splitlines())
    match = container.calc_intent(utterance)
    assert match["name"] == intent, (utterance, match)
    return match["entities"]


def _skill(lang):
    skill = object.__new__(RandomnessSkill)
    skill.speak_dialog = Mock()
    skill.play_audio = Mock()
    skill.gui = Mock()
    skill.log = Mock()
    skill._settings = {}
    patcher = patch.object(RandomnessSkill, "lang", new_callable=PropertyMock, return_value=lang)
    patcher.start()
    patch.object(RandomnessSkill, "enclosure", new_callable=PropertyMock, return_value=Mock()).start()
    return skill


def _rolls(handler, data):
    """The faces each die was rolled with: randint is patched to return its upper bound."""
    with patch("skill_randomness.randint", side_effect=lambda low, high: high) as randint:
        handler(Message("test", data))
    return [args.args[1] for args in randint.call_args_list]


@pytest.fixture(autouse=True)
def _stop_patches():
    yield
    patch.stopall()


@pytest.mark.parametrize("locale,lang,utterance,number,faces", MULTIPLE)
def test_rolls_the_asked_dice(locale, lang, utterance, number, faces):
    skill = _skill(lang)
    data = _slots(locale, "roll_multiple_dice", utterance)
    assert _rolls(skill.handle_roll_multiple_dice, data) == [faces] * number


@pytest.mark.parametrize("locale,lang,utterance,faces", SINGLE)
def test_rolls_a_die_with_the_asked_faces(locale, lang, utterance, faces):
    skill = _skill(lang)
    data = _slots(locale, "roll_single_die", utterance)
    assert _rolls(skill.handle_roll_single_die, data) == [faces]


@pytest.mark.parametrize("locale,lang,utterance,number", TWO_NUMBERS)
def test_first_number_of_the_slot_is_the_number_of_dice(locale, lang, utterance, number):
    skill = _skill(lang)
    data = _slots(locale, "roll_multiple_dice", utterance)
    assert _rolls(skill.handle_roll_multiple_dice, data) == [6] * number


@pytest.mark.xfail(strict=True, reason="https://github.com/TigreGotico/numtag/issues/244")
def test_a_couple_of_dice_are_two_dice():
    skill = _skill("en-us")
    data = _slots("en-US", "roll_multiple_dice", "roll a couple of dice")
    assert _rolls(skill.handle_roll_multiple_dice, data) == [6, 6]


@pytest.mark.parametrize("faces", ["", "gibberish", "zero", "half"])
def test_no_positive_faces_rolls_a_d6(faces):
    skill = _skill("en-us")
    assert _rolls(skill.handle_roll_single_die, {"faces": faces}) == [6]


@pytest.mark.parametrize("number", [None, "", "several", "zero"])
def test_no_positive_number_rolls_one_die(number):
    skill = _skill("en-us")
    data = {"number": number, "faces": "six"}
    assert _rolls(skill.handle_roll_multiple_dice, data) == [6]
