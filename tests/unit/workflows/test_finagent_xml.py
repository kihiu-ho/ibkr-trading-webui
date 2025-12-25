import os
import sys

sys.path.append(os.path.abspath("."))
sys.path.append(os.path.abspath("dags"))

import pytest

from dags.utils.finagent_xml import parse_finagent_xml


def test_parse_finagent_xml_parses_strings_and_maps():
    xml = """
    <output>
      <string name="analysis">hello</string>
      <map name="query">
        <string name="short_term_query">a</string>
        <string name="medium_term_query">b</string>
        <string name="long_term_query">c</string>
      </map>
    </output>
    """
    parsed = parse_finagent_xml(xml)
    assert parsed["analysis"] == "hello"
    assert parsed["query"]["short_term_query"] == "a"
    assert parsed["query"]["medium_term_query"] == "b"
    assert parsed["query"]["long_term_query"] == "c"


def test_parse_finagent_xml_raises_on_missing_output_tag():
    with pytest.raises(ValueError):
        parse_finagent_xml("not xml")


def test_parse_finagent_xml_sanitizes_unescaped_xml_chars_in_string_values():
    xml = """
    <output>
      <string name="analysis">5 < 10 & 3 > 2</string>
    </output>
    """
    parsed = parse_finagent_xml(xml)
    assert parsed["analysis"] == "5 < 10 & 3 > 2"


def test_parse_finagent_xml_does_not_double_escape_entities():
    xml = """
    <output>
      <string name="analysis">Tom &amp; Jerry</string>
    </output>
    """
    parsed = parse_finagent_xml(xml)
    assert parsed["analysis"] == "Tom & Jerry"


def test_parse_finagent_xml_recovers_from_unclosed_html_like_tags():
    xml = """
    <output>
      <string name="analysis">Hello <b>world</string>
    </output>
    """
    parsed = parse_finagent_xml(xml)
    assert parsed["analysis"] == "Hello <b>world"
