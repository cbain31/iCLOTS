"""Launch via python -m iclotspython, including --check and --version."""

from .launcher import main

if __name__ == "__main__":
    raise SystemExit(main())
