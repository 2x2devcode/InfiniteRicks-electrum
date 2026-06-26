#!/usr/bin/env python3
"""Launch InfiniteRicks Electrum Wallet."""

from __future__ import annotations

import logging
import sys
import traceback


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
        force=True,
    )


def _excepthook(exc_type, exc_value, exc_tb) -> None:
    logging.critical(
        "Unhandled exception:\n%s",
        "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
    )
    sys.__excepthook__(exc_type, exc_value, exc_tb)


def main() -> int:
    _configure_logging()
    sys.excepthook = _excepthook
    try:
        from infinitericks_wallet.gui.app import run_app

        return run_app()
    except Exception:
        logging.critical("Startup failed:\n%s", traceback.format_exc())
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
