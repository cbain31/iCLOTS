"""Modern clients for the existing tracking measurement policies."""

from iclotspython.application.tracking import TrackingRequest, run_tracking

from .video_screen import VelocityScreen


class TrackingScreen(VelocityScreen):
    service = staticmethod(run_tracking)

    def __init__(self, policy):
        self.policy = policy
        self.workflow_title = {
            "general": "Single-cell Tracking", "deformability": "Deformability",
            "transient_adhesion": "Transient Adhesion", "fluorescence": "Fluorescence Tracking",
        }[policy]
        super().__init__()
        if policy in {"deformability", "transient_adhesion"}:
            for name in ("search_range", "minimum_distance"):
                self.video_parameters[name].setEnabled(False)
                self.video_parameters[name].setToolTip("Derived from ROI width by the legacy scientific policy.")
        if policy != "transient_adhesion":
            self.video_parameters["maxmass"].setEnabled(False)

    def parameter_definitions(self):
        return (("diameter", "Cell diameter (odd pixels)", 15), ("minmass", "Minimum mass (a.u.)", 1000),
                ("maxmass", "Maximum mass, transient (a.u.)", 2500), ("search_range", "Search range (pixels)", 60),
                ("minimum_distance", "Distance threshold (pixels)", 100))

    def build_request(self):
        return TrackingRequest(self.video_input(), self.policy, self.calibration_spin.value(), self.fps_spin.value(),
            **{name: spin.value() for name, spin in self.video_parameters.items()}, roi=self.region())
