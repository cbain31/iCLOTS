# Synthetic accumulation fixture provenance

All fixtures are synthetic arrays or filenames. No microscopy images, biological measurements, human/animal data, personal identifiers, or sensitive metadata are included.

Arrays are row-major. JSON color objects use explicit `red`, `green`, and `blue` keys; production images are stored as BGR, with indices blue 0, green 1, red 2. Binary masks use 0/1. Intensity threshold examples use cutoff 50 and document the confirmed strict production rule `value > threshold`. Default calibration is 0.5 micrometres/pixel, so one pixel represents 0.25 square micrometres.

The empty, full, single-pixel, increasing, decreasing, and identical masks specify area and signed-change behavior. RGB fixtures specify overlap and disjoint counting. Irregular, disconnected, straight, multiple-horizontal, broken, and zero-area geometry fixtures specify denominator, connected-region, and controlled-failure behavior. `known_column_signal` has a deterministic 100%, 50%, 50%, 0% occupancy pattern in a two-row band. Filename examples expose lexical ordering and extension grouping.

Legacy expectations reproduce inspected source behavior. Intended expectations are controlled specifications only. Invariant expectations express geometry, scaling, ordering, or monotonic relationships.

