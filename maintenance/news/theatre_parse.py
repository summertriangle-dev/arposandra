import re, json

import dm_parse

CH_TAG = re.compile(r":th_ch([0-9]{4,})")


def dig_text_into_buffer(elem, buf):
    if elem.text:
        buf.append(elem.text)

    for child in elem:
        dig_text_into_buffer(child, buf)
    
    if elem.tail:
        buf.append(elem.tail)


class TheatreScriptWalkState(dm_parse.DMWalkState):
    def __init__(self, tag="article"):
        self.lines = []
        self.title = None
        self.char_refs = set()

        self.current_char = None
        self.buffer = []
    
    def ingest_text_internal(self, t_i):
        self.buffer.append(t_i)

    def ingest_element_internal(self, element):
        if element.tag in {"span", "align"}:
            dig_text_into_buffer(element, self.buffer)
        elif element.tag.startswith(":th_ch"):
            self.current_char = int(CH_TAG.match(element.tag).group(1))
        elif element.tag == ":dt_title_end":
            self.title = "".join(self.buffer)
            self.buffer = []
        elif element.tag == ":dt_line_end":
            self.lines.append({
                "character": self.current_char,
                "text": "".join(self.buffer)
            })
            self.char_refs.add(self.current_char)
            self.buffer = []

    def get_json(self):
        return json.dumps({
            "title": self.title,
            "lines": self.lines,
        }, ensure_ascii=False)