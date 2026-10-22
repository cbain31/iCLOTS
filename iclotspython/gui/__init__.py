"""Modern iCLOTS desktop interface.

Importing this package is side-effect free. Use ``python -m iclotspython.gui``
to construct and run the Qt application.
"""

from iclotspython import __version__

GUI_VERSION = f"{__version__} compatibility preview"

__all__ = ["GUI_VERSION"]

