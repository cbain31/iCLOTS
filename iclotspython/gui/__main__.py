"""Canonical ``python -m iclotspython.gui`` entrypoint."""

from .application import run


def main() -> int:
    """Launch one modern iCLOTS main window."""
    return run()


if __name__ == "__main__":
    raise SystemExit(main())

