import os
import sys

# Ensure Airflow-style DAG imports work in unit tests.
sys.path.append(os.path.abspath("."))
sys.path.append(os.path.abspath("dags"))

from dags.utils import finagent_prompts_v3 as prompts


def test_finagent_prompts_v3_preserves_core_placeholders():
    assert "$$asset_symbol$$" in prompts.TASK_DESCRIPTION_MARKET_INTELLIGENCE
    assert "$$latest_market_intelligence$$" in prompts.LATEST_MARKET_INTELLIGENCE_CONTEXT
    assert "$$past_market_intelligence$$" in prompts.PAST_MARKET_INTELLIGENCE_CONTEXT
    assert "$$past_market_intelligence_summary$$" in prompts.MARKET_INTELLIGENCE_SUMMARIES_CONTEXT
    assert "$$latest_market_intelligence_summary$$" in prompts.MARKET_INTELLIGENCE_SUMMARIES_CONTEXT
    assert "$$kline_path$$" in prompts.KLINE_CHART_DESCRIPTION
    assert "$$trading_path$$" in prompts.TRADING_CHART_DESCRIPTION


def test_finagent_prompts_v3_output_formats_are_xml():
    for template in (
        prompts.LATEST_MARKET_INTELLIGENCE_OUTPUT_FORMAT,
        prompts.PAST_MARKET_INTELLIGENCE_OUTPUT_FORMAT,
        prompts.LOW_LEVEL_REFLECTION_OUTPUT_FORMAT,
        prompts.HIGH_LEVEL_REFLECTION_OUTPUT_FORMAT,
        prompts.DECISION_OUTPUT_FORMAT,
    ):
        assert "<output>" in template
        assert "</output>" in template

