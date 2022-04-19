import json
from collections import defaultdict, namedtuple
import plac
import re

Sentence = namedtuple("Sentence", ("vec", "name", "value"))


def should_include_keywords(criteria_name):
    return criteria_name in ["member", "member_subunit", "member_group", "rarity", "attribute"]


def transmog(value, for_criteria):
    if for_criteria == "member":
        return value.split(maxsplit=1)[0]
    elif for_criteria == "member_subunit":
        return value.replace(" ", "")

    return value


def process_table(table):
    keywords = {}
    for (name, criteria) in table["criteria"].items():
        if not should_include_keywords(name):
            continue

        if "choices" in criteria:
            for choice in criteria["choices"]:
                if choice.get("separator"):
                    continue

                kwd = transmog((choice.get("display_name") or choice["name"]).lower(), name)
                # print(name, kwd)
                keywords[kwd] = {
                    "target": name,
                    "value": choice["value"],
                }

    return keywords


@plac.pos("output_file", "Where to write the definitions.")
@plac.pos("input_files", "Source files. Bootstrap comes first.")
def main(output_file, *input_files):
    assert len(input_files) >= 1

    d = {}
    for file in input_files:
        with open(file, "r") as f:
            d.update(process_table(json.load(f)))

    with open(output_file, "w") as outjs:
        json.dump(
            {"dictionary": d},
            outjs,
            indent=2,
            ensure_ascii=False,
        )


if __name__ == "__main__":
    plac.call(main)
