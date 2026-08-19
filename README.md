# skill-randomness

![Python](https://img.shields.io/badge/python-3.10-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![Python](https://img.shields.io/badge/python-3.13-blue.svg)
![Python](https://img.shields.io/badge/python-3.14-blue.svg)

## About

This OVOS skill handles chance-based requests. It makes a choice, rolls a die, flips a coin, and picks between two options.

## Install

```console
pip install ovos-skill-randomness
```

## Configuration

The skill accepts one property, `die_limit`. This property sets the maximum number of dice you can roll at once. The default is 16.

Set it in `~/.config/mycroft/skills/skill-randomness.openvoiceos/settings.json`:

```json
{
  "die_limit": 16
}
```

## Examples

- "Flip a coin"
- "Tell me my future"
- "Help me decide something"
- "Pick a number between 1 and 100"
- "Roll a die"
- "Roll 1 d 20"
- "Roll 6 d 8"
- "Roll a 20 sided die"
- "Roll 5 dice"
- "Roll 6, 8 sided dice"

## Related projects

- [OpenVoiceOS/OpenVoiceOS](https://github.com/OpenVoiceOS/OpenVoiceOS) — the OVOS voice assistant platform this skill runs on.
- [OpenVoiceOS/ovos-workshop](https://github.com/OpenVoiceOS/ovos-workshop) — the skill framework this skill builds on.

## Credits

- Mike Gray (@mikejgray)
- BuilderJer (@builderjer)

## Category

Games
Fun
Chance

## Tags

ovos skill games fun chance

## Attribution

The coin flipping sound came from [TheKnave at freesound.org](https://freesound.org/people/TheKnave/sounds/435621/). It is licensed under the [Creative Commons 4 License](https://creativecommons.org/licenses/by-nc/4.0/).

The fortune teller sound came from [LittleRainySeasons at freesound.org](https://freesound.org/people/LittleRainySeasons/sounds/335354/). It is licensed under the [Creative Commons 0 License](https://creativecommons.org/publicdomain/zero/1.0/).

The dice rolling sound came from [dermotte at freesound.org](https://freesound.org/people/dermotte/sounds/220741/). It is licensed under the [Creative Commons 4 License](https://creativecommons.org/licenses/by/4.0/).

## License

This skill is available under the [MIT License](LICENSE).
