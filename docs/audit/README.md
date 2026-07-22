# iCLOTS development audits

These reports document the pre-modernization assessment of the legacy
iCLOTS repository and its published velocity-profile workflow.

## Repository audit

The initial repository audit mapped application workflows, dependencies,
packaging duplication, scientific-risk areas, and current architectural
coupling.

## Historical velocity validation

Archived control and sepsis workbooks were linked directly to Nature
Communications Figure 4C and Figure 4D at publication precision. The
representative sepsis profile was flatter than control across multiple
prespecified shape metrics.

## Raw-video reproduction

The checked-out legacy implementation under a modern OpenCV environment
partially reproduced the archived numerical outputs and preserved the
main representative sepsis/control trends. Exact historical feature-level
reproduction remains unresolved because the complete original parameter
set and dependency environment were not preserved.

Raw videos and historical workbooks are maintained outside Git under the
locally ignored `data/` directory.