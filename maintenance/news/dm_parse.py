#!/usr/bin/env python3
import sys
import json
import uuid
import re
import base64

from lxml.etree import Element, SubElement, ProcessingInstruction, HTMLParser, tostring

def font_size_norm(x):
    """the web font size is different from the game client's - try to
    approximate how it would look without having to know the actual value."""
    try:
        x = int(x)
    except ValueError:
        return "100%"
    ratio = x / 24
    return f"{int(ratio * 100)}%"

def make_link_inert(l):
    mask = base64.urlsafe_b64encode(l.encode("utf8")).decode("ascii").strip("=")
    return f"/api/private/intersitial?p={mask}"

class DMWalkState(object):
    INLINE_TAGS = {
        "color": ("color", lambda x: x),
        "align": ("text-align", lambda x: x),
        # XXX: different enough to warrant another elif?
        "b": ("font-weight", lambda x: "bold"),
        "size": ("font-size", font_size_norm),
    }

    def __init__(self, tag="article"):
        self.root = Element(tag)
        self.image_references = set()
        self.card_master_references = set()

    def ingest_text_internal(self, t_i):
        if len(self.root) == 0:
            self.root.text = "".join(
                (self.root.text or "", t_i))
        else:
            self.root[-1].tail = "".join(
                (self.root[-1].tail or "", t_i))

    def ingest_text(self, t):
        if not t:
            return self

        self.ingest_text_internal(t)
        return self

    def ingest_element_internal(self, element):
        if element.tag in {"color", "align", "size", "b"}:
            if element.tag == "align":
                t = "div"
            else:
                t = "span"
            sub = DMWalkState(t).ingest_element(element).commit()
            csstag, transform = self.INLINE_TAGS.get(element.tag, (element.tag, lambda x: x))
            sub.set("style", f"{csstag}: {transform(element.get('value'))}")
            self.root.append(sub)
        elif element.tag == "subtitle":
            sub = SubElement(self.root, "h2")
            sub.text = element.get("text")
        elif element.tag == "signboard":
            sbe = SubElement(self.root, "div", {"class": "signboard-element"})
            SubElement(sbe, "h3").text = element.get("title")
            SubElement(sbe, "p").text = element.get("message")
        elif element.tag in {"sprite", "img"}:
            sbe = SubElement(self.root, "img", {
                "class": f"dm-src-{element.tag}",
                "src": f"/api/private/ii?p={element.get('src')}",
                "width": element.get("width"),
                # Removed for good reason
                # "height": element.get("height")
            })
            self.image_references.add(element.get("src"))
        elif element.tag == "card":
            sub = ProcessingInstruction("asi-include-card", f"card-id:{element.get('value')}")
            # We put this newline here to preserve the block-ness of the original element.
            sub.tail = "\n"
            self.root.append(sub)

            try:
                self.card_master_references.add(int(element.get("value")))
            except ValueError:
                pass
        elif element.tag == "linkbutton":
            # FIXME: combine with normal button?
            sub = SubElement(self.root, "div", {
                "class": "button-wrapper"
            })
            SubElement(sub, "a", {
                "href": make_link_inert(element.get("link_text")),
                "class": "btn btn-primary",
            }).text = element.get("button_text")
        elif element.tag == "button":
            sub = SubElement(self.root, "div", {
                "class": "button-wrapper"
            })
            SubElement(sub, "button", {
                "class": "btn btn-primary",
                "disabled": "disabled"
            }).text = element.get("button_text")
        elif element.tag in {"hr"}:
            SubElement(self.root, element.tag)
        else:
            sub = SubElement(self.root, "div")
            sub.set("style", "background: red; color: white")
            sub.text = f"DMWalkState: ignored an element of type {element.tag}"

    def ingest_element(self, element):
        self.ingest_text(element.text)

        for i in element:
            self.ingest_element_internal(i)
            self.ingest_text(i.tail)

        return self

    def commit(self):
        return self.root

# The DM align tag is written like <align="center">...</align>
# This isn't valid and gets swallowed by lxml so we have to fix it
# here :(
FIX_TAGS_REGEX = re.compile(rb"<align=\"([^\"]+)\">|<align='([^']+)'>", re.IGNORECASE)

def fix_tags_repl(m):
    q_type = chr(m.group(0)[len("<align=")])
    st = (m.group(1) or m.group(2)).decode("utf8")
    return "<align value={0}{1}{0}>".format(q_type, st).encode("ascii")

FIX_BLIND_TIMESTAMP_CODES = re.compile(r"\uEC92(1|2|4|5) ([0-9]+)")

def fix_blind_ts(m):
    return f'<?asi-blind-ts t:{m.group(1)};v:{m.group(2)}?>'

def fix_tags(dmtext):
    if dmtext.startswith(b"\xee\xb2\x92"):
        has_blinds = True
        dmtext = dmtext[3:]
    else:
        has_blinds = False
    tagged = FIX_TAGS_REGEX.sub(fix_tags_repl, dmtext)
    return tagged, has_blinds

def dm_to_html(dmtext):
    mark = str(uuid.uuid4())
    dmtext, has_blinds = fix_tags(dmtext)
    p = HTMLParser()
    p.feed(f"<div id='{mark}'>".encode("ascii"))
    p.feed(dmtext)
    p.feed(b"</div>")

    doc = p.close()
    root = doc.find(f".//div[@id = '{mark}']")

    synth_root = DMWalkState()
    synth_root.ingest_element(root)

    text = tostring(synth_root.commit(), encoding="utf-8").decode("utf8")
    if has_blinds:
        text = FIX_BLIND_TIMESTAMP_CODES.sub(fix_blind_ts, text)

    return (text, 
        list(synth_root.card_master_references) or None,
        list(synth_root.image_references) or None)
