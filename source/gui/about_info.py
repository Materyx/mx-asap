"""
In-app and About-dialog constants: URLs, contact address, and links to the open-source repository.

The detailed About text is fully localized in ``source/resources/strings.csv`` (keys under ``about.*``).
"""

from __future__ import annotations

from typing import Final

# Public GitHub org/repo for releases, source, and license.
URL_MXASAP: Final[str] = "https://github.com/Materyx/mx-asap"

# MIT license (full text) in the public repository; branch may be adjusted to match the default branch.
URL_MIT: Final[str] = "https://github.com/Materyx/mx-asap/blob/main/LICENSE"

# Issue tracker for the application.
URL_ISSUES: Final[str] = "https://github.com/Materyx/mx-asap/issues"

# Company website.
URL_SITE: Final[str] = "https://www.materyx.ru"

# Primary contact e-mail and its ``mailto:`` URL (for About and external handlers).
ABOUT_EMAIL: Final[str] = "info@materyx.ru"
ABOUT_EMAIL_MAILTO: Final[str] = f"mailto:{ABOUT_EMAIL}"
