"""Helpers for parsing FinAgent paper XML prompt outputs."""

from __future__ import annotations

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

