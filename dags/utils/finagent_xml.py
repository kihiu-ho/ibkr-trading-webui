"""Helpers for parsing FinAgent paper XML prompt outputs."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional
from xml.etree import ElementTree


def extract_output_xml(text: str) -> str:
    """Extract the <output>...</output> block from a larger model response."""
    if not text:
        raise ValueError("Empty FinAgent XML response")

    start = text.find("<output")
    end = text.rfind("</output>")
    if start == -1 or end == -1:
        raise ValueError("Missing <output> root element in FinAgent XML response")

    return text[start : end + len("</output>")].strip()

_XML_ENTITY_RE = re.compile(r"&(#\d+|#x[0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]+);")


def sanitize_finagent_output_xml(xml_text: str) -> str:
    """Best-effort sanitizer for model XML output.

    Large language models occasionally emit XML-looking text inside <string> values
    (for example: "5 < 10 & 3 > 2"), which breaks strict XML parsing.

    This sanitizer escapes:
      - '<' that do not start a known FinAgent tag (<output>, <string>, <map>)
      - '&' that are not already part of an XML entity
    """

    if not xml_text:
        return xml_text

    out: list[str] = []
    stack: list[str] = []
    i = 0
    in_tag = False
    length = len(xml_text)

    known_tags = {"output", "string", "map"}

    def _allowed(tag_name: str, closing: bool) -> bool:
        current = stack[-1] if stack else None

        if current is None:
            return (not closing) and tag_name == "output"
        if current == "output":
            return (closing and tag_name == "output") or ((not closing) and tag_name in {"string", "map"})
        if current == "map":
            return (closing and tag_name == "map") or ((not closing) and tag_name == "string")
        if current == "string":
            return closing and tag_name == "string"
        return False

    while i < length:
        ch = xml_text[i]

        if in_tag:
            out.append(ch)
            if ch == ">":
                in_tag = False
            i += 1
            continue

        if ch == "<":
            close = xml_text.find(">", i + 1)
            if close == -1:
                out.append("&lt;")
                i += 1
                continue

            token = xml_text[i + 1 : close].strip()
            if not token:
                out.append("&lt;")
                i += 1
                continue

            closing = token.startswith("/")
            body = token[1:].lstrip() if closing else token
            tag_name = body.split()[0].rstrip("/")

            if tag_name not in known_tags or not _allowed(tag_name, closing):
                out.append("&lt;")
                i += 1
                continue

            in_tag = True
            out.append("<")
            i += 1

            if closing:
                if stack and stack[-1] == tag_name:
                    stack.pop()
            else:
                stack.append(tag_name)
            continue

        if ch == "&":
            match = _XML_ENTITY_RE.match(xml_text, i)
            if match:
                out.append(match.group(0))
                i += len(match.group(0))
            else:
                out.append("&amp;")
                i += 1
            continue

        out.append(ch)
        i += 1

    return "".join(out)


def parse_finagent_xml(text: str) -> Dict[str, Any]:
    """Parse FinAgent XML output into a nested dict.

    Expected shape:
      <output>
        <string name="...">...</string>
        <map name="...">
          <string name="...">...</string>
        </map>
      </output>
    """

    xml_text = extract_output_xml(text)
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as exc:
        sanitized = sanitize_finagent_output_xml(xml_text)
        if sanitized != xml_text:
            try:
                root = ElementTree.fromstring(sanitized)
            except ElementTree.ParseError:
                raise ValueError(f"Invalid FinAgent XML: {exc}") from exc
        else:
            raise ValueError(f"Invalid FinAgent XML: {exc}") from exc

    if root.tag != "output":
        raise ValueError(f"Unexpected root tag: {root.tag}")

    parsed: Dict[str, Any] = {}
    for child in root:
        if child.tag == "string":
            name = child.attrib.get("name")
            if not name:
                continue
            parsed[name] = (child.text or "").strip()
        elif child.tag == "map":
            map_name = child.attrib.get("name")
            if not map_name:
                continue
            entries: Dict[str, str] = {}
            for item in child:
                if item.tag != "string":
                    continue
                key = item.attrib.get("name")
                if not key:
                    continue
                entries[key] = (item.text or "").strip()
            parsed[map_name] = entries

    return parsed


def get_required(parsed: Dict[str, Any], key: str) -> str:
    value = parsed.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing required FinAgent XML field: {key}")
    return value.strip()


def get_required_map(parsed: Dict[str, Any], key: str) -> Dict[str, str]:
    value = parsed.get(key)
    if not isinstance(value, dict) or not value:
        raise ValueError(f"Missing required FinAgent XML map: {key}")
    out: Dict[str, str] = {}
    for map_key, map_value in value.items():
        if isinstance(map_value, str):
            out[map_key] = map_value.strip()
    if not out:
        raise ValueError(f"Missing required FinAgent XML map entries: {key}")
    return out


def safe_get_str(parsed: Dict[str, Any], key: str) -> Optional[str]:
    value = parsed.get(key)
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None
