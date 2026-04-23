"""
Configurable axis mappings for matplotlib views.

Defaults follow the ASAP workflow requested for stage 1 and can be swapped later.
"""

from __future__ import annotations

from typing import Literal

IsothermSeries = Literal[
    "relative_pressure",
    "pressure_mmhg",
    "vol_adsorbed_cc_g_stp",
]

BJHSeries = Literal[
    "average_diameter_a",
    "incremental_pore_volume_cc_g",
    "cumulative_pore_volume_cc_g",
    "incremental_pore_area_sq_m_g",
    "cumulative_pore_area_sq_m_g",
]

XISOTHERM_DEFAULT: IsothermSeries = "vol_adsorbed_cc_g_stp"
YISOTHERM_DEFAULT: IsothermSeries = "relative_pressure"

XBJH_DEFAULT: BJHSeries = "incremental_pore_area_sq_m_g"
YBJH_DEFAULT: BJHSeries = "average_diameter_a"
