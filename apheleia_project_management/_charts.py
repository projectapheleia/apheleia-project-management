import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

from ._utils import default_end_date

BAR_WIDTH = 0.62
""" Fraction of the row height used by each Gantt bar """

SCALES = {
    "Monthly"   : ("MS", "Month starting",   "%b %Y", "%b %Y"),
    "Quarterly" : ("QS", "Quarter starting", "%b %Y", "%b %Y"),
    "Yearly"    : ("YS", "Year",             "%Y",    "%Y"),
}
""" Time scales offered for charts: pandas frequency, x label, tick format, hover format """

def aggregate_by_period(df : pd.DataFrame, x : str, groups : list, value : str, scale : str, how : str) -> pd.DataFrame:
    """
    Re-bin a dataframe of dated values into months, quarters or years

    :param df: Dataframe
    :type df: pd.DataFrame
    :param x: Column holding the dates
    :type x: str
    :param groups: Columns to keep separate (e.g. the resource)
    :type groups: list
    :param value: Column holding the values
    :type value: str
    :param scale: One of SCALES
    :type scale: str
    :param how: "sum" to add values up in each period (flows such as effort), or
                "last" to take the final value in each period (levels such as work remaining)
    :type how: str
    :return: Dataframe with the same columns, x now holding the start of each period
    :rtype: pd.DataFrame
    """

    tmp = df.sort_values(x).copy()
    tmp[x] = pd.to_datetime(tmp[x]).dt.to_period(SCALES[scale][0][0]).dt.start_time

    grouped = tmp.groupby([x] + list(groups), as_index=False, sort=False)[value]
    return grouped.sum() if how == "sum" else grouped.last()

INK = "ink"
""" Trace meta marking a line, marker or text that is drawn in the text colour of the theme, so it stays readable on dark themes """

PALETTE = px.colors.qualitative.Plotly + px.colors.qualitative.Dark24
""" Colours cycled through when giving each name its own colour """

EFFORT_COLORS = {
    "Spent" : "#636EFA",
    "Remaining" : "#AAB2FC",
    "Spent past estimate" : "#D62839",
    "Remaining past estimate" : "#F4A3A8",
}
""" Colours for task effort. Blues are effort within the original estimate, reds effort past it """

def color_map(names) -> dict:
    """
    Give each name its own colour, so the same name has the same colour on every chart

    :param names: Names in the order they should be coloured
    :return: Dictionary of name to colour
    :rtype: dict
    """

    names = list(dict.fromkeys(names))
    return {n : PALETTE[i % len(PALETTE)] for i, n in enumerate(names)}

FONT = "Segoe UI, Inter, -apple-system, Helvetica Neue, Arial, sans-serif"
""" Font used on all charts """

def _merge(target : dict, changes : dict) -> dict:
    """
    Merge changes into a plotly property dictionary, as plotly's update does: dictionaries are merged, other values
    replace what is there and None removes the property. Dictionaries are copied in, so the changes are not shared

    :param target: Dictionary to change in place
    :param changes: Changes
    :return: target
    """

    for k, v in changes.items():
        if v is None:
            target.pop(k, None)
        elif isinstance(v, dict):
            if not isinstance(target.get(k), dict):
                target[k] = {}
            _merge(target[k], v)
        else:
            target[k] = v
    return target

def _template_colorway() -> list:
    """ Colours plotly express gives groups that have no colour of their own: the colorway of the default template """

    return list(pio.templates[pio.templates.default].layout.colorway)

def _groups(df : pd.DataFrame, column : str, order : list=None) -> tuple[list, list]:
    """
    Split a dataframe into groups by the values of a column, in the order plotly express uses: the given order, then
    the order the values appear in. Rows with no value are left out

    :param df: Dataframe
    :param column: Column to group by
    :param order: Optional order of values. Values not in it come after, in the order they appear
    :return: Every value in order (including given values that do not appear), and a list of (value, rows)
    """

    values = list(dict.fromkeys(list(order or []) + df[column].unique().tolist()))
    present = df[column].notna()
    groups = [(v, df[present & (df[column] == v)]) for v in values if not (isinstance(v, float) and pd.isna(v))]
    return values, [(v, g) for v, g in groups if len(g)]

def _group_colors(values : list, colors : dict=None) -> dict:
    """
    Colour of each group, as plotly express gives them: the given colour, or the next colour of the template's
    colorway, counting every colour given so far

    :param values: Every value in order (see _groups)
    :param colors: Optional dictionary of value to colour
    :return: Dictionary of value to colour
    """

    sequence = _template_colorway()
    mapping = dict(colors or {})
    for v in values:
        if v not in mapping:
            mapping[v] = sequence[len(mapping) % len(sequence)]
    return mapping

def _bar_trace(name, color : str, **props) -> dict:
    """ A bar trace with the properties plotly express gives each group """

    return dict(type="bar", name=name, legendgroup=name, showlegend=True, textposition="auto", xaxis="x", yaxis="y",
                marker=dict(color=color, pattern=dict(shape="")), **props)

def _shade_traces(traces : list, width : float) -> list:
    """
    Shading for the bars of a list of traces (plain dictionaries). See _shade_bars

    :param traces: Traces, changed in place
    :param width: Width of each bar, in axis units
    :return: The traces with the shading added: the shadows, then the traces, then the depth and gloss bands
    """

    def overlay(trace, color, w, offset):
        t = _merge({}, trace)
        return _merge(t, dict(
            marker=dict(color=color, line=dict(width=0), cornerradius=4),
            width=w,
            offset=offset,
            hoverinfo="skip",
            hovertemplate=None,
            showlegend=False,
            text=None,
            name="",
        ))

    base = -width / 2
    shadows, glosses = [], []
    for trace in traces:
        if trace.get("type") != "bar":
            continue
        color = trace.get("marker", {}).get("color")
        _merge(trace, dict(
            width=width,
            offset=base,
            opacity=1,
            marker=dict(color=color, line=dict(color="rgba(0,0,0,0.35)", width=1), cornerradius=4),
            # Simple bubble: white background, black text, outline matching the bar
            hoverlabel=dict(bgcolor="#ffffff", bordercolor=color, font=dict(family=FONT, size=13, color="#000000")),
        ))

        # Drop shadow - slightly offset from the bar
        shadows.append(overlay(trace, "rgba(15,29,51,0.22)", width, base + 0.14 * width))

        # Depth - dark band over the trailing third
        glosses.append(overlay(trace, "rgba(0,0,0,0.16)", width * 0.38, base + width * 0.62))

        # Gloss - light band over the leading half
        glosses.append(overlay(trace, "rgba(255,255,255,0.34)", width * 0.42, base + width * 0.04))

    # Shadows draw first and gloss last
    return shadows + traces + glosses

def _shade_bars(fig : go.Figure, width : float) -> None:
    """
    Add shading effects to the bars of a bar figure (horizontal or vertical).

    Plotly has no native gradient fill, so each coloured bar is layered with
      - a soft offset drop shadow underneath
      - a translucent white highlight along one edge (gloss)
      - a translucent dark band along the opposite edge (depth)
    The overlays copy the geometry of the real bars, so they track zoom / pan,
    and are excluded from hover so tooltips still describe the real bar.

    The work is done on plain dictionaries (see _shade_traces) and the traces put back in one go, which is much
    quicker than copying and adding plotly trace objects one at a time.

    Widths and offsets are measured across the bar, i.e. in row units for
    horizontal bars and in x units for vertical bars. The figure must use
    barmode overlay.

    :param fig: Figure to modify in place
    :type fig: go.Figure
    :param width: Width of each bar, in axis units
    :type width: float
    """

    traces = [t.to_plotly_json() for t in fig.data]
    fig.data = ()
    fig.add_traces(_shade_traces(traces, width))

def style_axes(fig : go.Figure) -> None:
    """
    Apply the common look (fonts, gridlines, background) to a figure

    :param fig: Figure to modify in place
    :type fig: go.Figure
    """

    layout = base_layout()
    xaxis, yaxis = layout.pop("xaxis"), layout.pop("yaxis")
    fig.update_layout(**layout)
    fig.update_xaxes(**xaxis)
    fig.update_yaxes(**yaxis)

def base_layout() -> dict:
    """
    The common look (fonts, gridlines, background) as a layout, for figures built in one go rather than styled
    with style_axes. Each call gives a new dictionary, which can be changed

    :return: Layout dictionary with font, background, hover label and x and y axis settings
    :rtype: dict
    """

    return dict(
        font=dict(family=FONT, size=13, color="#1c2433"),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#f6f8fc",
        hoverlabel=dict(bgcolor="#ffffff", font=dict(family=FONT, size=13, color="#000000"), align="left"),
        xaxis=dict(gridcolor="#dfe5f0", gridwidth=1, linecolor="#b7c2d6", zeroline=False),
        yaxis=dict(gridcolor="#e8ecf4", gridwidth=1, linecolor="#b7c2d6", zeroline=False),
    )

LEGEND_WIDTH = 190
""" Extra chart width needed for a legend placed to the right of the plot """

MAX_PLOT_WIDTH = 1000
""" Widest a bar chart's plot area can be and still fit the page. Wider charts scroll """

MARKER_PLOT_WIDTH = 1000
""" Approximate width of a Gantt plot area in pixels, used to decide when marker labels would overlap """

MARKER_CHAR_WIDTH = 7
""" Approximate width of a character of a marker label in pixels """

MARKER_PADDING = 12
""" Space left between marker labels in pixels """

MARKER_ROW_HEIGHT = 16
""" Vertical step between rows of marker labels in pixels """

LEGEND_OUTSIDE = dict(x=1.01, xanchor="left", y=1, yanchor="top",
                      bgcolor="rgba(255,255,255,0.9)", bordercolor="#b7c2d6", borderwidth=1)
""" Legend placed to the right of the plot """

def gantt(  df : pd.DataFrame,
            title : str,
            x_start : tuple[str, str],
            x_end : tuple[str, str],
            y: tuple[str, str],
            markers: dict[str, pd.Timestamp]=None,
            bar_height=50,
            description: str=None,
            link_key: str=None,
            colors: dict=None,
            show_legend: bool=False,
            milestones: tuple[str, str]=None,
            windows: dict[str, tuple[pd.Timestamp, pd.Timestamp]]=None,
            opacity: str=None) -> px.timeline:
    """
    Generate Gantt chart from dataframe

    :param df: Dataframe
    :type df: pd.DataFrame
    :param title: Title of the chart
    :type title: str
    :param x_start: Tuple containing column and label for start dates
    :type x_start: tuple[str, str]
    :param x_end: Tuple containing column and label for end dates
    :type x_end: tuple[str, str]
    :param y: Tuple containing column and label for y axis
    :type y: tuple[str, str]
    :param markers: Dictionary of markers to add to the chart
    :type markers: dict[str, pd.Timestamp]
    :param bar_height: Height of each bar
    :type bar_height: int
    :param description: Optional column holding text shown when hovering over a bar
    :type description: str
    :param link_key: Optional container type (e.g. "project"). Clicking a bar then opens the
                     html page of the container named by the bar's y value
    :type link_key: str
    :param colors: Optional dictionary of y value to colour (see color_map)
    :type colors: dict
    :param show_legend: Show a key of the colour of each y value
    :type show_legend: bool
    :param milestones: Optional tuple of the columns holding the milestone name and milestone date of each
                       row. A diamond is drawn on the row at the date of the milestone
    :type milestones: tuple[str, str]
    :param windows: Optional dictionary of name to (start, end) for milestones that span a period. Each is drawn
                    as two dotted vertical lines joined by a horizontal line, and may overlap others
    :type windows: dict[str, tuple[pd.Timestamp, pd.Timestamp]]
    :param opacity: Optional column holding the opacity (0 to 1) of each bar, e.g. to fade periods of part time availability
    :type opacity: str
    :return: Gantt chart
    :rtype: px.timeline
    """

    # Create a new copy of the date
    # Insert an end date (max of the default and largest in data)
    horizon = default_end_date()
    df_new = df.fillna(value={"end": horizon})
    default_end = max(df_new[x_end[0]].max(), horizon)
    df_new = df.fillna(value={"end": default_end})

    # Hover text, built explicitly so it is always populated
    def fmt(v, empty):
        return v.strftime("%Y-%m-%d") if pd.notna(v) else empty

    df_new = df_new.copy()
    df_new["_start"] = [fmt(v, "not set") for v in df_new[x_start[0]]]
    df_new["_end"] = [fmt(v, "") for v in df_new[x_end[0]]]
    df_new.loc[df[x_end[0]].isna().to_numpy(), "_end"] = "open ended"
    if description is not None and description in df_new.columns:
        df_new["_desc"] = df_new[description].fillna("").astype(str)
    else:
        df_new["_desc"] = ""
    if opacity is not None and opacity in df_new.columns:
        df_new["_opacity"] = df_new[opacity].fillna(1).astype(float)
    else:
        df_new["_opacity"] = 1.0

    # Several bars can share a row, e.g. the availability periods of a resource
    n_rows = max(df_new[y[0]].nunique(), 1) if len(df_new) else 0

    # The bars, one trace for each row name, as px.timeline makes them. The figure is built in one go from plain
    # data at the end, which is much quicker than changing a plotly figure a piece at a time
    custom = [y[0], "_start", "_end", "_desc", "_opacity"]
    start = pd.to_datetime(df_new[x_start[0]])
    length = (pd.to_datetime(df_new[x_end[0]]) - start) // pd.Timedelta(milliseconds=1)
    timeline = df_new.assign(_base=start, _length=length)
    names, groups = _groups(timeline, y[0])
    group_colors = _group_colors(names, colors)
    hover = "<b>%{customdata[0]}</b><br>%{customdata[1]} to %{customdata[2]}<br>%{customdata[3]}<extra></extra>"
    traces = [_bar_trace(name, group_colors[name], orientation="h", base=g["_base"].to_numpy(), x=g["_length"].to_numpy(),
                         y=g[y[0]].to_numpy(), customdata=g[custom].to_numpy(), hovertemplate=hover)
              for name, g in groups]

    layout = dict(
        xaxis=dict(anchor="y", domain=[0.0, 1.0], type="date"),
        yaxis=dict(anchor="x", domain=[0.0, 1.0], title=dict(text=y[1]), categoryorder="array",
                   categoryarray=list(reversed(names))),
        legend=dict(title=dict(text=y[1]), tracegroupgap=0),
        margin=dict(t=60),
        barmode="overlay",
    )
    if title:
        layout["title"] = dict(text=title)
    if link_key is not None:
        layout["meta"] = {"link_key": link_key}

    rows = 1
    shapes, annotations = [], []
    markers = markers or {}
    windows = {k : v for k, v in (windows or {}).items() if pd.notna(v[0]) and pd.notna(v[1])}
    if markers or windows:
        # Put labels that would overlap the previous one on a higher row
        points = [v for v in markers.values() if pd.notna(v)] + [d for w in windows.values() for d in w]
        x_min = min([df_new[x_start[0]].min()] + points)
        x_max = max([df_new[x_end[0]].max()] + points)
        span = max((x_max - x_min).total_seconds(), 1)
        plot_height = n_rows * bar_height
        row_ends = []

        def place(first, last, name):
            start = (first - x_min).total_seconds() / span
            end = max((last - x_min).total_seconds() / span,
                      start + (len(str(name)) * MARKER_CHAR_WIDTH + MARKER_PADDING) / MARKER_PLOT_WIDTH)
            row = next((i for i, e in enumerate(row_ends) if start >= e), len(row_ends))
            if row == len(row_ends):
                row_ends.append(end)
            else:
                row_ends[row] = end
            return row

        items = [(v, v, k, False) for k, v in markers.items() if pd.notna(v)]
        items += [(w[0], w[1], k, True) for k, w in windows.items()]
        for first, last, k, is_window in sorted(items, key=lambda i: (i[0], i[1])):
            row = place(first, last, k)
            if not is_window:
                # A dashed line labelled at the top right, as add_vline draws it
                x = first.timestamp() * 1000
                shapes.append(dict(type="line", xref="x", yref="y domain", x0=x, x1=x, y0=0, y1=1,
                                   line=dict(color="#d62839", dash="dash", width=2)))
                annotations.append(dict(xref="x", yref="y domain", x=x, y=1, xanchor="left", yanchor="top",
                                        showarrow=False, text=k, yshift=20 + row * MARKER_ROW_HEIGHT,
                                        font=dict(color="#d62839", size=12)))
                continue

            # Window: dotted line at each end, joined by a horizontal line above the plot
            top = 1 + (20 + row * MARKER_ROW_HEIGHT) / max(plot_height, 1)
            line = dict(color="#d62839", width=2, dash="dot")
            for x in (first, last):
                shapes.append(dict(type="line", xref="x", yref="paper", x0=x, x1=x, y0=0, y1=top, line=dict(line)))
            shapes.append(dict(type="line", xref="x", yref="paper", x0=first, x1=last, y0=top, y1=top,
                               line=dict(color="#d62839", width=2)))
            annotations.append(dict(xref="x", yref="paper", x=first, y=top, text=k, showarrow=False,
                                    xanchor="left", yanchor="bottom", xshift=4, font=dict(color="#d62839", size=12)))
        rows = max(len(row_ends), 1)
    if shapes:
        layout["shapes"] = shapes
    if annotations:
        layout["annotations"] = annotations

    # Opacity of each bar, set before shading so the shading is faded with the bar
    if opacity is not None:
        for trace in traces:
            trace["marker"]["opacity"] = [float(cd[4]) for cd in trace["customdata"]]

    _merge(layout, base_layout())
    traces = _shade_traces(traces, BAR_WIDTH)

    # Milestone each row is working towards
    if milestones is not None and milestones[0] in df_new.columns and milestones[1] in df_new.columns:
        ms = df_new[df_new[milestones[1]].notna()]
        if not ms.empty:
            traces.append(dict(
                type="scatter",
                x=ms[milestones[1]],
                y=ms[y[0]],
                mode="markers",
                marker=dict(symbol="diamond", size=16, color="#d62839", line=dict(color="white", width=1.5)),
                customdata=ms[[milestones[0], milestones[1]]].assign(**{milestones[1] : ms[milestones[1]].dt.strftime("%Y-%m-%d")}).to_numpy(),
                hovertemplate="<b>%{y}</b><br>Milestone %{customdata[0]}: %{customdata[1]}<extra></extra>",
                showlegend=False,
            ))

    _merge(layout, dict(
        barmode="overlay",
        xaxis=dict(title=dict(text=f"{x_start[1]} - {x_end[1]}")),
        yaxis=dict(title=dict(text=f"{y[1]}")),
        showlegend=show_legend,
        legend=LEGEND_OUTSIDE | dict(title=dict(text=y[1])),
        title= {'x':0.5, 'xanchor': 'center', 'yanchor': 'top'},
        margin=(dict(l=50, r=50, t=50 + (rows - 1) * MARKER_ROW_HEIGHT, b=50)),
        colorway=px.colors.qualitative.Alphabet,
        height=((n_rows*bar_height) + 100 + (rows - 1) * MARKER_ROW_HEIGHT),
        autosize=True,
    ))

    # Choose a tick spacing so labels stay readable whatever the date range
    span_days = (df_new[x_end[0]].max() - df_new[x_start[0]].min()).days
    if span_days < 3650:
        dtick, tickformat = "M3", "%b\n%Y"
    else:
        dtick, tickformat = "M12", "%Y"

    _merge(layout["xaxis"], dict(
        dtick=dtick,
        tickformat=tickformat,
        ticklabelmode="period",
        tickangle=0,
        automargin=True
    ))

    # Tell the html page to offer a scale select box for the ticks
    meta = dict(layout.get("meta") or {})
    meta["scale_ticks"] = True
    meta["scale_default"] = "Quarterly" if dtick == "M3" else "Yearly"
    layout["meta"] = meta

    fig = go.Figure(data=traces, layout=layout)
    return fig

def stacked_bar(df : pd.DataFrame,
                title : str,
                x : tuple[str, str],
                y : tuple[str, str],
                color : str,
                height=1000,
                bar_width=50,
                descriptions: dict=None,
                link_key: str=None,
                tickformat: str=None,
                hover_date_format: str="%d %b %Y",
                colors: dict=None,
                legend_outside: bool=False,
                link_to: tuple=None) -> px.timeline:
    """
    Generate a stacked bar chart from a dataframe

    :param df: Dataframe
    :type df: pd.DataFrame
    :param title: Title of the chart
    :type title: str
    :param x: Tuple containing column and label for x axis
    :type x: tuple[str, str]
    :param y: Tuple containing column and label for y axis
    :type y: tuple[str, str]
    :param color: Column to color by
    :type color: str
    :param height: Height of the chart
    :type height: int
    :param bar_width: Width of each bar
    :type bar_width: int
    :param descriptions: Optional dictionary of colour group to text shown when hovering over its bars
    :type descriptions: dict
    :param link_key: Optional container type (e.g. "resource"). Clicking a bar then opens the
                     html page of the container named by the bar's colour group
    :type link_key: str
    :param tickformat: Optional d3 format for the x axis labels
    :type tickformat: str
    :param hover_date_format: d3 format for dates shown when hovering
    :type hover_date_format: str
    :param colors: Optional dictionary of colour group to colour (see color_map)
    :type colors: dict
    :param legend_outside: Place the key to the right of the plot instead of over it
    :type legend_outside: bool
    :param link_to: Optional (container type, name). Clicking any bar then opens that container's page
    :type link_to: tuple
    :return: Stacked bar chart
    :rtype: px.timeline
    """

    # The bars, one trace for each colour group, as px.bar makes them. The figure is built in one go from plain
    # data at the end, which is much quicker than changing a plotly figure a piece at a time
    names, groups = _groups(df, color, list(colors) if colors else None)
    group_colors = _group_colors(names, colors)
    traces = [_bar_trace(name, group_colors[name], orientation="v", x=g[x[0]].to_numpy(), y=g[y[0]].to_numpy())
              for name, g in groups]
    layout = dict(
        xaxis=dict(anchor="y", domain=[0.0, 1.0], title=dict(text=x[1])),
        yaxis=dict(anchor="x", domain=[0.0, 1.0], title=dict(text=y[1])),
        legend=dict(title=dict(text=color), tracegroupgap=0),
        margin=dict(t=60),
    )
    if title:
        layout["title"] = dict(text=title)
    _merge(layout, base_layout())

    # Plotly cannot layer overlays on a stacked bar, so stack by hand:
    # give every bar an explicit base and draw in overlay mode
    totals = {}
    for trace in traces:
        bases = []
        for xv, yv in zip(trace["x"], trace["y"], strict=True):
            bases.append(totals.get(xv, 0))
            totals[xv] = totals.get(xv, 0) + (yv or 0)
        trace["base"] = bases

    # Bar width in axis units (milliseconds for dates)
    xs = pd.Series(df[x[0]].unique()).sort_values()
    if pd.api.types.is_datetime64_any_dtype(xs):
        gap = xs.diff().min()
        width = (gap if pd.notna(gap) else pd.Timedelta(days=30)).total_seconds() * 1000 * 0.7
    else:
        width = 0.7

    layout["barmode"] = "overlay"

    # Hover text, built explicitly so it is always populated
    descriptions = descriptions or {}
    for trace in traces:
        trace["customdata"] = [[descriptions.get(trace["name"], "")]] * len(trace["x"])
        trace["hovertemplate"] = (f"<b>%{{fullData.name}}</b><br>{x[1]}: %{{x|{hover_date_format}}}"
                                  f"<br>{y[1]}: %{{y:.4~g}}<br>%{{customdata[0]}}<extra></extra>")

    if link_key is not None:
        layout["meta"] = {"link_key": link_key, "link_by": "trace"}
    if link_to is not None:
        layout["meta"] = {"link_key": link_to[0], "link_to": link_to[1]}

    traces = _shade_traces(traces, width)

    # Clean up the X-Axis formatting
    _merge(layout["xaxis"], dict(tickmode="array", tickvals=df[x[0]].unique(), tickangle=-45))
    if tickformat is not None:
        layout["xaxis"]["tickformat"] = tickformat

    # Fill the card, unless the bars need more room than it has, in which case the chart scrolls
    plot_width = bar_width * len(df[x[0]].unique())
    if plot_width > MAX_PLOT_WIDTH:
        _merge(layout, dict(width=plot_width + 200 + (LEGEND_WIDTH if legend_outside else 0), autosize=False))
    else:
        layout["autosize"] = True

    # Update layout
    _merge(layout, dict(
        height=height,
        legend=dict(title=dict(text=color.split(".")[-1].replace("_", " ").title())),
        margin=(dict(l=50, r=50, t=50, b=50)),
        colorway=px.colors.qualitative.Alphabet,
    ))
    _merge(layout, dict(legend=LEGEND_OUTSIDE if legend_outside else dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#b7c2d6",
            borderwidth=1
        )))

    fig = go.Figure(data=traces, layout=layout)
    return fig

__all__ = [
    "gantt",
    "stacked_bar"
]
