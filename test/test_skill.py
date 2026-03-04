# pylint: disable=missing-docstring
import shutil
from json import dumps
from os import environ, getenv, makedirs
from os.path import join, dirname, isdir
from unittest.mock import Mock, patch, PropertyMock
import pytest
from ovos_bus_client.message import Message
from ovos_plugin_manager.skills import find_skill_plugins
from ovos_utils.fakebus import FakeBus

from skill_randomness import RandomnessSkill


@pytest.fixture(scope="session")
def test_skill(test_skill_id="skill-ovos-randomness.openvoiceos", bus=FakeBus()):
    # Get test skill
    bus.emitter = bus.ee
    bus.run_forever()
    skill_entrypoint = getenv("TEST_SKILL_ENTRYPOINT")
    if not skill_entrypoint:
        skill_entrypoints = list(find_skill_plugins().keys())
        assert test_skill_id in skill_entrypoints
        skill_entrypoint = test_skill_id

    skill = RandomnessSkill(skill_id=test_skill_id, bus=bus)
    skill.speak = Mock()
    skill.speak_dialog = Mock()
    skill.play_audio = Mock()
    skill.gui = Mock()
    mock_enclosure = Mock()
    enclosure_patcher = patch.object(type(skill), "enclosure", new_callable=PropertyMock, return_value=mock_enclosure)
    enclosure_patcher.start()
    yield skill
    enclosure_patcher.stop()
    shutil.rmtree(join(dirname(__file__), "skill_fs"), ignore_errors=False)


@pytest.fixture(scope="function")
def reset_skill_mocks(test_skill):
    test_skill.speak.reset_mock()
    test_skill.speak_dialog.reset_mock()
    test_skill.play_audio.reset_mock()
    test_skill.gui.reset_mock()
    test_skill.enclosure.reset_mock()  # resets the mock_enclosure returned by the property


class TestRandomnessSkill:
    test_fs = join(dirname(__file__), "skill_fs")
    data_dir = join(test_fs, "data")
    conf_dir = join(test_fs, "config")
    environ["XDG_DATA_HOME"] = data_dir
    environ["XDG_CONFIG_HOME"] = conf_dir
    if not isdir(test_fs):
        makedirs(data_dir)
        makedirs(conf_dir)

    with open(join(conf_dir, "mycroft.conf"), "w", encoding="utf-8") as f:
        f.write(dumps({"Audio": {"backends": {"ocp": {"active": False}}}}))

    def test_flip_a_coin(self, test_skill, reset_skill_mocks):
        test_skill.handle_flip_a_coin(Message("flip-a-coin.intent"))
        test_skill.speak_dialog.assert_called_once()
        dialog, data = test_skill.speak_dialog.call_args[0][0], test_skill.speak_dialog.call_args[1]["data"]
        assert dialog == "coin-result"
        assert data["result"] in ("heads", "tails")

    def test_pick_a_number_with_range(self, test_skill, reset_skill_mocks):
        test_skill.handle_pick_a_number(Message("pick-a-number.intent", data={"lower": "3", "upper": "7"}))
        test_skill.speak_dialog.assert_called_once()
        dialog, data = test_skill.speak_dialog.call_args[0][0], test_skill.speak_dialog.call_args[1]["data"]
        assert dialog == "number-result"
        assert 3 <= data["number"] <= 7

    def test_pick_a_number_no_range(self, test_skill, reset_skill_mocks):
        test_skill.handle_pick_a_number(Message("pick-a-number.intent", data={}))
        dialogs_called = [c[0][0] for c in test_skill.speak_dialog.call_args_list]
        assert "number-range-not-specified" in dialogs_called
        assert "number-result" in dialogs_called
        result_call = next(c for c in test_skill.speak_dialog.call_args_list if c[0][0] == "number-result")
        assert 1 <= result_call[1]["data"]["number"] <= 10

    def test_roll_single_die_default(self, test_skill, reset_skill_mocks):
        test_skill.handle_roll_single_die(Message("roll-single-die.intent", data={"faces": "6"}))
        test_skill.speak_dialog.assert_called_once()
        dialog, data = test_skill.speak_dialog.call_args[0][0], test_skill.speak_dialog.call_args[1]["data"]
        assert dialog == "die-result"
        assert 1 <= data["result"] <= 6

    def test_roll_single_die_custom_faces(self, test_skill, reset_skill_mocks):
        test_skill.handle_roll_single_die(Message("roll-single-die.intent", data={"faces": "20"}))
        data = test_skill.speak_dialog.call_args[1]["data"]
        assert 1 <= data["result"] <= 20

    @pytest.mark.parametrize("bad_value", [None, False])
    def test_roll_single_die_extract_number_fallback(self, test_skill, reset_skill_mocks, bad_value):
        with patch("skill_randomness.extract_number", return_value=bad_value):
            test_skill.handle_roll_single_die(Message("roll-single-die.intent", data={"faces": "six"}))
        data = test_skill.speak_dialog.call_args[1]["data"]
        assert 1 <= data["result"] <= 6  # fell back to d6

    @pytest.mark.parametrize("bad_value", [None, False])
    def test_roll_multiple_dice_extract_number_fallback(self, test_skill, reset_skill_mocks, bad_value):
        with patch("skill_randomness.extract_number", return_value=bad_value):
            test_skill.handle_roll_multiple_dice(Message("roll-multiple-dice.intent", data={"number": "several", "faces": "six"}))
        data = test_skill.speak_dialog.call_args[1]["data"]
        rolls = data["result_string"].split(", ")
        assert len(rolls) == 1  # fell back to 1 die
        assert 1 <= int(rolls[0]) <= 6  # fell back to d6

    def test_roll_multiple_dice(self, test_skill, reset_skill_mocks):
        test_skill.handle_roll_multiple_dice(Message("roll-multiple-dice.intent", data={"number": "3", "faces": "6"}))
        data = test_skill.speak_dialog.call_args[1]["data"]
        rolls = data["result_string"].split(", ")
        assert len(rolls) == 3
        assert all(1 <= int(r) <= 6 for r in rolls)
        assert data["result_total"] == str(sum(int(r) for r in rolls))

    def test_roll_multiple_dice_over_limit(self, test_skill, reset_skill_mocks):
        over_limit = test_skill.die_limit + 5
        test_skill.handle_roll_multiple_dice(Message("roll-multiple-dice.intent", data={"number": str(over_limit), "faces": "6"}))
        dialogs_called = [c[0][0] for c in test_skill.speak_dialog.call_args_list]
        assert "over-dice-limit" in dialogs_called
        result_call = next(c for c in test_skill.speak_dialog.call_args_list if c[0][0] == "multiple-die-result")
        rolls = result_call[1]["data"]["result_string"].split(", ")
        assert len(rolls) == test_skill.die_limit

    def test_make_a_choice(self, test_skill, reset_skill_mocks):
        test_skill.get_response = Mock(side_effect=["pizza", "tacos"])
        test_skill.handle_make_a_choice_intent(Message("make-a-choice.intent"))
        dialog, data = test_skill.speak_dialog.call_args[0][0], test_skill.speak_dialog.call_args[1]["data"]
        assert dialog == "choice-result"
        assert data["choice"] in ("pizza", "tacos")

    def test_fortune_teller(self, test_skill, reset_skill_mocks):
        test_skill.get_response = Mock(return_value="will it rain tomorrow")
        test_skill.handle_fortune_teller(Message("fortune-teller.intent"))
        test_skill.speak_dialog.assert_called_once()
        assert test_skill.speak_dialog.call_args[0][0] == "fortune-result"
        assert test_skill.speak_dialog.call_args[0][1]["answer"] in ("yes", "no")


def test_skill_is_a_valid_plugin():
    assert "skill-ovos-randomness.openvoiceos" in find_skill_plugins()


if __name__ == "__main__":
    pytest.main()
