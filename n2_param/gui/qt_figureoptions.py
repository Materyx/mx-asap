"""
Localizable Matplotlib figure options dialog (fork of ``qt_editor.figureoptions``).

Replaces the stock English-only labels and tab titles; behavior matches Matplotlib
``figure_edit`` so the apply-callback and field order stay consistent.

Based on Matplotlib 3.8+ ``figureoptions.py``; the apply logic is unchanged.
"""

from __future__ import annotations

from collections.abc import Callable
from itertools import chain
from typing import TypeAlias

from matplotlib import cbook, cm, colors as mcolors, image as mimage, markers
from matplotlib.backends.qt_compat import QtGui
from matplotlib.backends.qt_editor import _formlayout
from matplotlib.dates import DateConverter, num2date

Tr: TypeAlias = Callable[[str], str]

_MARKERS = markers.MarkerStyle.markers


def _linestyles_map(tr: Tr) -> dict[str, str]:
    return {
        "-": tr("figure_options.ls_solid"),
        "--": tr("figure_options.ls_dashed"),
        "-.": tr("figure_options.ls_dashdot"),
        ":": tr("figure_options.ls_dotted"),
        "None": tr("figure_options.ls_none"),
    }


def _drawstyles_map(tr: Tr) -> dict[str, str]:
    return {
        "default": tr("figure_options.draw_default"),
        "steps-pre": tr("figure_options.draw_steps_pre"),
        "steps": tr("figure_options.draw_steps_pre"),
        "steps-mid": tr("figure_options.draw_steps_mid"),
        "steps-post": tr("figure_options.draw_steps_post"),
    }


def _axis_section_html(name: str, tr: Tr) -> str:
    """Build the bold per-axis group heading; falls back to ``X-Axis``-style if no CSV key."""
    n = (name or "").lower()
    if not n:
        return "<b>Axis</b>"
    key = f"figure_options.axis_section_{n}"
    t = tr(key)
    if t == key or not t.strip():
        return f"<b>{name.title()}-Axis</b>"
    return t


def figure_edit(axes, parent, tr: Tr) -> None:
    """
    Open the Matplotlib figure-options form with localized field labels and tabs.

    Parameters:
        axes: The :class:`matplotlib.axes.Axes` to edit.
        parent: Qt parent; stored as ``_fedit_dialog`` on the toolbar.
        tr: Map ``strings.csv`` keys to translated text for the current locale.
    """
    if not callable(tr):
        raise TypeError("tr must be callable")
    sep = (None, None)
    linestyles = _linestyles_map(tr)
    drawstyles = _drawstyles_map(tr)

    def convert_limits(lim, converter) -> list:
        if isinstance(converter, DateConverter):
            return list(map(num2date, lim))
        return list(map(float, lim))

    axis_map = axes._axis_map
    axis_limits = {
        name: tuple(convert_limits(getattr(axes, f"get_{name}lim")(), axis.converter))
        for name, axis in axis_map.items()
    }
    general = [
        (tr("figure_options.field_figure_title"), axes.get_title()),
        sep,
        *chain.from_iterable(
            [
                (
                    (None, _axis_section_html(name, tr)),
                    (tr("figure_options.field_min"), axis_limits[name][0]),
                    (tr("figure_options.field_max"), axis_limits[name][1]),
                    (tr("figure_options.field_label"), axis.get_label().get_text()),
                    (tr("figure_options.field_scale"), [axis.get_scale(), "linear", "log", "symlog", "logit"]),
                    sep,
                )
                for name, axis in axis_map.items()
            ],
        ),
        (tr("figure_options.regenerate_legend"), False),
    ]
    axis_converter = {name: axis.converter for name, axis in axis_map.items()}
    axis_units = {name: axis.get_units() for name, axis in axis_map.items()}

    labeled_lines: list = []
    for line in axes.get_lines():
        label = line.get_label()
        if label == "_nolegend_":
            continue
        labeled_lines.append((label, line))
    curves: list = []

    def prepare_data(d: dict, init) -> list:
        if init not in d:
            d = {**d, init: str(init)}
        name2short = {name: short for short, name in d.items()}
        short2name = {short: name for name, short in name2short.items()}
        canonical_init = name2short[d[init]]
        return [canonical_init] + sorted(
            short2name.items(), key=lambda short_and_name: short_and_name[1]
        )

    for label, line in labeled_lines:
        color = mcolors.to_hex(mcolors.to_rgba(line.get_color(), line.get_alpha()), keep_alpha=True)
        ec = mcolors.to_hex(mcolors.to_rgba(line.get_markeredgecolor(), line.get_alpha()), keep_alpha=True)
        fc = mcolors.to_hex(mcolors.to_rgba(line.get_markerfacecolor(), line.get_alpha()), keep_alpha=True)
        curvedata = [
            (tr("figure_options.field_label"), label),
            sep,
            (None, tr("figure_options.section_line_html")),
            (tr("figure_options.field_line_style"), prepare_data(dict(linestyles), line.get_linestyle())),
            (tr("figure_options.field_draw_style"), prepare_data(dict(drawstyles), line.get_drawstyle())),
            (tr("figure_options.field_width"), line.get_linewidth()),
            (tr("figure_options.field_color_rgba"), color),
            sep,
            (None, tr("figure_options.section_marker_html")),
            (tr("figure_options.field_style"), prepare_data(dict(_MARKERS), line.get_marker())),
            (tr("figure_options.field_size"), line.get_markersize()),
            (tr("figure_options.field_face_color_rgba"), fc),
            (tr("figure_options.field_edge_color_rgba"), ec),
        ]
        curves.append([curvedata, label, ""])
    has_curve = bool(curves)

    labeled_mappables: list = []
    for mappable in [*axes.images, *axes.collections]:
        m_label = mappable.get_label()
        if m_label == "_nolegend_" or mappable.get_array() is None:
            continue
        labeled_mappables.append((m_label, mappable))
    mappables: list = []
    cmaps = [(cmap, name) for name, cmap in sorted(cm._colormaps.items())]
    for m_label, mappable in labeled_mappables:
        cmap = mappable.get_cmap()
        if cmap not in cm._colormaps.values():
            cmaps = [(cmap, cmap.name), *cmaps]
        low, high = mappable.get_clim()
        mappabledata = [
            (tr("figure_options.field_label"), m_label),
            (tr("figure_options.field_colormap"), [cmap.name] + cmaps),
            (tr("figure_options.field_min_value"), low),
            (tr("figure_options.field_max_value"), high),
        ]
        if hasattr(mappable, "get_interpolation"):
            interpolations = [(name, name) for name in sorted(mimage.interpolations_names)]
            mappabledata.append(
                (
                    tr("figure_options.field_interpolation"),
                    [mappable.get_interpolation(), *interpolations],
                )
            )
            interpolation_stages = ["data", "rgba"]
            mappabledata.append(
                (
                    tr("figure_options.field_interpolation_stage"),
                    [mappable.get_interpolation_stage(), *interpolation_stages],
                )
            )
        mappables.append([mappabledata, m_label, ""])
    has_sm = bool(mappables)

    tab_axes = tr("figure_options.tab_axes")
    tab_curves = tr("figure_options.tab_curves")
    tab_mappables = tr("figure_options.tab_mappables")
    curves_tab_comment = tr("figure_options.tab_curves_comment")
    datalist: list = [(general, tab_axes, "")]
    if curves:
        datalist.append((curves, tab_curves, curves_tab_comment))
    if mappables:
        datalist.append((mappables, tab_mappables, ""))

    def apply_callback(data) -> None:
        orig_limits = {name: getattr(axes, f"get_{name}lim")() for name in axis_map}
        general_ = data.pop(0)
        curves_ = data.pop(0) if has_curve else []
        mappables_ = data.pop(0) if has_sm else []
        if data:
            raise ValueError("Unexpected field")
        title = general_.pop(0)
        axes.set_title(title)
        generate_legend = general_.pop()
        for i, (aname, axis) in enumerate(axis_map.items()):
            axis_min = general_[4 * i]
            axis_max = general_[4 * i + 1]
            axis_label = general_[4 * i + 2]
            axis_scale = general_[4 * i + 3]
            if axis.get_scale() != axis_scale:
                getattr(axes, f"set_{aname}scale")(axis_scale)
            axis._set_lim(axis_min, axis_max, auto=False)
            axis.set_label_text(axis_label)
            axis.converter = axis_converter[aname]
            axis.set_units(axis_units[aname])
        for index, curve in enumerate(curves_):
            line = labeled_lines[index][1]
            (lab, linestyle, drawstyle, linewidth, color, marker, markersize, mfc, mec) = curve
            line.set_label(lab)
            line.set_linestyle(linestyle)
            line.set_drawstyle(drawstyle)
            line.set_linewidth(linewidth)
            rgba = mcolors.to_rgba(color)
            line.set_alpha(None)
            line.set_color(rgba)
            if marker != "none":
                line.set_marker(marker)
                line.set_markersize(markersize)
                line.set_markerfacecolor(mfc)
                line.set_markeredgecolor(mec)
        for index, mappable_settings in enumerate(mappables_):
            mappable = labeled_mappables[index][1]
            if len(mappable_settings) == 6:
                lab, cma, lo, hi, inter, inter_stage = mappable_settings
                mappable.set_interpolation(inter)
                mappable.set_interpolation_stage(inter_stage)
            elif len(mappable_settings) == 4:
                lab, cma, lo, hi = mappable_settings
            else:
                msg = f"Unexpected mappable settings count: {len(mappable_settings)}"
                raise ValueError(msg)
            mappable.set_label(lab)
            mappable.set_cmap(cma)
            mappable.set_clim(*sorted([lo, hi]))
        if generate_legend:
            draggable = None
            ncols = 1
            if axes.legend_ is not None:
                old_legend = axes.get_legend()
                if old_legend is not None:
                    draggable = old_legend._draggable is not None
                    ncols = old_legend._ncols
            new_legend = axes.legend(ncols=ncols)
            if new_legend is not None:
                new_legend.set_draggable(draggable)
        figure = axes.get_figure()
        figure.canvas.draw()
        for aname in axis_map:
            if getattr(axes, f"get_{aname}lim")() != orig_limits[aname]:
                if figure.canvas.toolbar is not None:
                    figure.canvas.toolbar.push_current()
                break

    _formlayout.fedit(
        datalist,
        title=tr("figure_options.dialog_title"),
        parent=parent,
        icon=QtGui.QIcon(str(cbook._get_data_path("images", "qt4_editor_options.svg"))),
        apply=apply_callback,
    )
