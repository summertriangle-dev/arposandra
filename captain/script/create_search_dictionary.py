import json
from collections import defaultdict, namedtuple
import plac
import re

Sentence = namedtuple("Sentence", ("vec", "name", "value"))


class Dictionary(object):
    def __init__(self):
        self.high = set()
        self.word_bag = set()
        self.seen_sentences = set()
        self.sentences = []
        self.map_word_to_sentences = defaultdict(list)

    def clean(self, sentence):
        sentence = re.sub(r"[^a-zA-Z0-9 \-]", "", sentence.lower())
        return sentence

    def add_sentence(self, sentence, criteria_name, criteria_value):
        association = (sentence, criteria_name, criteria_value)
        if association in self.seen_sentences:
            return

        self.seen_sentences.add(association)
        words = tuple(self.clean(sentence).split())
        self.sentences.append(Sentence(words, criteria_name, criteria_value))
        self.high.add(words[0])
        self.word_bag.update(words)

    def finalize(self):
        self.sentences.sort()
        smap = [*enumerate(self.sentences)]
        for word in self.word_bag:
            self.map_word_to_sentences[word] = [i for i, v in smap if word in v.vec]

    def process_table(self, table):
        for (name, criteria) in table["criteria"].items():
            if "choices" in criteria:
                for choice in criteria["choices"]:
                    print(name, choice.get("display_name") or choice["name"])
                    self.add_sentence(
                        choice.get("display_name") or choice["name"], name, choice["value"]
                    )


@plac.pos("output_file", "Where to write the definitions.")
@plac.pos("input_files", "Source files. Bootstrap comes first.")
def main(output_file, *input_files):
    assert len(input_files) >= 1

    d = Dictionary()
    for file in input_files:
        with open(file, "r") as f:
            d.process_table(json.load(f))

    d.finalize()

    word_map = sorted(d.map_word_to_sentences.items())
    with open(output_file, "w") as outjs:
        json.dump(
            {
                "words": [k for k, v in word_map],
                "bag": [{"sentences": v, "priority": 2 if k in d.high else 1} for k, v in word_map],
                "sen": [x._asdict() for x in d.sentences],
            },
            outjs,
            indent=2,
            ensure_ascii=False,
        )


if __name__ == "__main__":
    plac.call(main)
