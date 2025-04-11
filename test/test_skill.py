# pylint: disable=missing-docstring
import pytest
import shutil
from json import dumps
from os import environ, getenv, makedirs
from os.path import join, dirname, isdir
from unittest.mock import Mock, patch
from typing import Any, Generator
from ovos_plugin_manager.skills import find_skill_plugins
from ovos_utils.fakebus import FakeBus

from skill_randomness import RandomnessSkill


@pytest.fixture(scope="session")
def test_skill(test_skill_id="skill-ovos-randomness.openvoiceos", bus=FakeBus()) -> Generator[RandomnessSkill, Any, None]:
    # Get test skill
    bus.emitter = bus.ee
    bus.run_forever()
    skill = RandomnessSkill(skill_id=test_skill_id, bus=bus)
    skill.speak = Mock()
    skill.speak_dialog = Mock()
    skill.play_audio = Mock()
    yield skill
    shutil.rmtree(join(dirname(__file__), "skill_fs"), ignore_errors=False)


@pytest.fixture(scope="function")
def reset_skill_mocks(test_skill):
    # Reset mocks before each test
    test_skill.speak.reset_mock()
    test_skill.speak_dialog.reset_mock()
    test_skill.play_audio.reset_mock()


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

    def test_nada(self, test_skill):
        assert True


def test_skill_is_a_valid_plugin():
    assert "skill-ovos-randomness.openvoiceos" in find_skill_plugins()


@patch('skill_randomness.choice')
def test_skill_flip_coin(choice_mock, test_skill):
    choice_mock.return_value = 'heads'
    test_skill.handle_flip_a_coin('flip a coin')
    test_skill.speak_dialog.assert_called_with('coin-result', data={'result': 'heads'})


if __name__ == "__main__":
    pytest.main()
