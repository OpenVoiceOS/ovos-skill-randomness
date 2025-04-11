"""A skill for all kinds of chance - make a choice, roll a die, flip a coin, etc."""
from os.path import dirname
from random import randint, choice
from typing import List

from icepool import Die, d

from ovos_bus_client.message import Message
from ovos_workshop.decorators import intent_handler
from ovos_number_parser import extract_number
from ovos_workshop.skills import OVOSSkill


class RandomnessSkill(OVOSSkill):
    """A skill for all kinds of chance - make a choice, roll a die, flip a coin, etc."""

    @property
    def die_limit(self):
        return self.settings.get("die_limit", 16)

    @intent_handler("make-a-choice.intent")
    def handle_make_a_choice_intent(self, message: Message):  # pylint: disable=unused-argument
        """Decide between two things."""
        first_choice = self.get_response("first-choice") or "the first one"
        second_choice = self.get_response("second-choice") or "the second one"
        try:
            result = Die([first_choice, second_choice]).sample()
        except TypeError:
            result = Die(first_choice, second_choice).sample()
        self.speak_dialog("choice-result", data={"choice": result})
        self.gui.show_text(result)
        self.enclosure.eyes_blink("b")
        self.enclosure.mouth_text(result)

    @intent_handler("pick-a-number.intent")
    def handle_pick_a_number(self, message: Message):
        """Pick a number between two numbers."""
        lower_bound = message.data.get("lower", "")
        upper_bound = message.data.get("upper", "")
        self.log.debug(f"Lower: {lower_bound}, Upper: {upper_bound}")
        try:
            upper_bound = round(float(upper_bound))
            lower_bound = round(float(lower_bound))
        except ValueError:
            lower_bound = 1
            upper_bound = 10
            self.speak_dialog("number-range-not-specified")
        result = randint(lower_bound, upper_bound)
        self.speak_dialog("number-result", data={"number": result})
        self.gui.show_text(str(result))
        self.enclosure.eyes_spin()
        self.enclosure.mouth_text(str(result))

    @intent_handler("flip-a-coin.intent")
    def handle_flip_a_coin(self, message: Message):  # pylint: disable=unused-argument
        """Flip a coin."""
        self.play_audio(f"{dirname(__file__)}/coin-flip.wav")
        heads_list = self.voc_list("heads")
        tails_list = self.voc_list("tails")
        heads_word = choice(heads_list)
        tails_word = choice(tails_list)
        try:
            result = Die([heads_word, tails_word]).sample()
        except TypeError:
            result = Die(heads_word, tails_word).sample()
        self.speak_dialog("coin-result", data={"result": result})
        self.gui.show_text(result)
        self.enclosure.system_blink(3)
        self.enclosure.mouth_text(result)

    @intent_handler("fortune-teller.intent")
    def handle_fortune_teller(self, message: Message):  # pylint: disable=unused-argument
        """Get a random fortune."""
        self.play_audio(f"{dirname(__file__)}/magic.mp3")
        fortune = self.get_response("fortune-query")
        yes_list = self.voc_list("yes")
        no_list = self.voc_list("no")
        yes_word = choice(yes_list)
        no_word = choice(no_list)
        try:
            answer = Die([yes_word, no_word]).sample()
        except TypeError:
            answer = Die(yes_word, no_word).sample()
        self.speak_dialog("fortune-result", {"answer": answer})
        fortune_with_answer = f"{fortune}? ...{answer}"
        self.gui.show_text(fortune_with_answer)
        self.enclosure.eyes_spin()
        self.enclosure.mouth_text(fortune_with_answer)

    @intent_handler("roll-single-die.intent")
    def handle_roll_single_die(self, message: Message):
        """Roll a single die."""
        faces = extract_number(message.data.get("faces", "6"), lang=self.lang)
        self.play_audio(f"{dirname(__file__)}/die-roll.wav")
        self.log.debug(f"Rolling a die with {faces} faces")
        result = Die(d(int(faces))).sample()
        self.speak_dialog("die-result", data={"result": result})
        self.gui.show_text(str(result))
        self.enclosure.eyes_spin()
        self.enclosure.mouth_text(str(result))

    @intent_handler("roll-multiple-dice.intent")
    def handle_roll_multiple_dice(self, message: Message):
        """Roll multiple dice."""
        number = extract_number(message.data.get("number"), lang=self.lang)
        faces = extract_number(message.data.get("faces", "6"), lang=self.lang)
        self.play_audio(f"{dirname(__file__)}/die-roll.wav")
        if number > self.die_limit:
            self.speak_dialog("over-dice-limit", data={"number": self.die_limit})
            number = self.die_limit
        self.log.debug(f"Rolling {number} dice with {faces} faces")
        result_list: List[int] = []
        for _ in range(1, int(number) + 1):
            val = Die(d(int(faces))).sample()
            result_list.append(val)
        self.speak_dialog("multiple-die-result", data={"result_string": ", ".join([str(x) for x in result_list]), "result_total": str(sum(result_list))})
