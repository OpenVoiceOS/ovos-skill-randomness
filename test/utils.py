from os import listdir
from padacioso.bracket_expansion import expand_parentheses


def construct_test_yaml(intent: str, entity: str) -> None:
    [
        print(f"    - {x.replace('{entity}', entity)}:\n        - entity: {entity}")
        for x in expand_parentheses(intent)
    ]

for file in listdir("skill_randomness/locale/en-US/intents"):
    if file.endswith(".intent"):
        print(f"  {file}:")
        with open(f"skill_randomness/locale/en-US/intents/{file}", "r") as f:
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue
                construct_test_yaml(line.strip(), file.split(".")[0])

print("\n\ndialog:")
for file in listdir("skill_randomness/locale/en-US/dialog"):
    if file.endswith(".dialog"):
        print(f"  - {file.split('.')[-2]}")

print("\n\nintents:")
print("  padatious:")
for file in listdir("skill_randomness/locale/en-US/intents"):
    if file.endswith(".intent"):
        print(f"    - {file}")
