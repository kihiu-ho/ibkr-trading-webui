"""Smoke tests for the Workflow Symbols template to ensure key UI hooks exist."""
from pathlib import Path

import pytest

TEMPLATE_PATH = Path("frontend/templates/workflow_symbols.html")


@pytest.fixture(scope="module")
def workflow_symbols_template() -> str:
    return TEMPLATE_PATH.read_text()


def test_modal_steps_and_active_workflow_guard_present(workflow_symbols_template: str) -> None:
    assert 'modalStep === 1' in workflow_symbols_template
    assert 'modalStep === 2' in workflow_symbols_template
    assert 'modalStep === 3' in workflow_symbols_template
    assert 'selectedWorkflows.some((wf) => wf.is_active)' in workflow_symbols_template


def test_selected_workflow_cards_include_json_validation(workflow_symbols_template: str) -> None:
    assert 'config.config_json' in workflow_symbols_template
    assert 'config.json_error' in workflow_symbols_template
    assert 'validateJson(config)' in workflow_symbols_template


def test_workflow_symbols_component_defines_state_helpers(workflow_symbols_template: str) -> None:
    assert 'function workflowSymbols()' in workflow_symbols_template
    assert 'addWorkflow(workflow)' in workflow_symbols_template
    assert 'moveWorkflow(index, delta)' in workflow_symbols_template
    assert 'validateSelectedWorkflows()' in workflow_symbols_template
