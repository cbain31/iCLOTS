"""Opt-in full local sequences; operability only, sources remain read-only."""

import pytest

from iclotspython.gui.workflow_screen import MultiscaleScreen
from tests.gui.test_gui_roi_workflow import _process_until
from tests.support.local_test_data import directory_snapshot
from tests.support.output_factory import workspace_output_directory

pytestmark = [pytest.mark.local_data, pytest.mark.integration, pytest.mark.gui]


@pytest.mark.parametrize("mode", ["device", "microchannel"])
@pytest.mark.parametrize("subgroup", ["SCD", "SCD_with_drug"])
def test_local_multiscale_sequence(local_test_data_root, qt_app, mode, subgroup):
    directory = local_test_data_root / "Multiscale_accumulation_microfluidic-w-microchannels" / subgroup
    if not directory.is_dir():
        pytest.skip("Selected multiscale dataset absent")
    paths = sorted(directory.glob("combinedimg_*.png"), key=lambda p: int(p.stem.rsplit("_", 1)[-1]))
    if len(paths) != 9:
        pytest.skip("Expected nine-frame sequence absent")
    before = directory_snapshot(directory)
    screen = MultiscaleScreen(mode)
    try:
        screen.add_images(paths=[str(p) for p in paths])
        screen.channel_widgets[next(iter(screen.channel_widgets))][0].setChecked(True)
        screen.start_analysis()
        _process_until(qt_app, lambda: screen._thread is None, timeout=40)
        assert screen.result is not None, screen.validation_feedback.text()
        assert screen.result.table("Measurements").rows
        with workspace_output_directory() as output:
            screen.destination_edit.setText(str(output))
            screen.export_xlsx.setChecked(True)
            assert screen.perform_export()[0].status.value == "success"
    finally:
        screen.shutdown()
        assert directory_snapshot(directory) == before
