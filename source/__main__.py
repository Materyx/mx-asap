"""
CLI entrypoint for launching Materyx ASAP Analyzer (mx-asap).

Configures logging and starts the Qt event loop.
"""

from __future__ import annotations

import logging
import sys

from source.application import create_application, run_main_window


def main() -> None:
    """Configure logging and launch the GUI."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logger = logging.getLogger(__name__)
    app = create_application(sys.argv)
    exit_code = run_main_window(app)
    logger.info("Application exiting with code %s", exit_code)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
