"""Repository-wide pytest policy for optional local-data tests."""

from __future__ import annotations

import re

import pytest

from tests.support.local_test_data import (
    LocalTestDataUnavailable,
    configured_test_data_root,
    roi_surface_sequence,
)


def _local_data_was_explicitly_selected(config: pytest.Config) -> bool:
    expression = config.getoption("markexpr") or ""
    return (
        re.search(r"\blocal_data\b", expression) is not None
        and re.search(r"\bnot\s+local_data\b", expression) is None
    )


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Exclude local datasets unless the marker is named explicitly."""
    if _local_data_was_explicitly_selected(config):
        return
    selected = []
    deselected = []
    for item in items:
        if item.get_closest_marker("local_data") is None:
            selected.append(item)
        else:
            deselected.append(item)
    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected


@pytest.fixture(scope="session")
def local_test_data_root():
    """Return the configured ignored dataset root or skip cleanly."""
    try:
        return configured_test_data_root()
    except LocalTestDataUnavailable as exc:
        pytest.skip(str(exc))


@pytest.fixture(scope="session")
def roi_surface_paths(local_test_data_root):
    """Return the ordered Healthy ROI surface sequence or skip cleanly."""
    try:
        return roi_surface_sequence(local_test_data_root)
    except LocalTestDataUnavailable as exc:
        pytest.skip(str(exc))

