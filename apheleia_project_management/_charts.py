import copy

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

def _shade_bars(fig : go.Figure, width : float) -> None:
    """
    Add shading effects to the bars of a bar figure (horizontal or vertical).

    Plotly has no native gradient fill, so each coloured bar is layered with
      - a soft offset drop shadow underneath
      - a translucent white highlight along one edge (gloss)
      - a translucent dark band along the opposite edge (depth)
    The overlays copy the geometry of the real bars, so they track zoom / pan,
    and are excluded from hover so tooltips still describe the real bar.

    Widths and offsets are measured across the bar, i.e. in row units for
    horizontal bars and in x units for vertical bars. The figure must use
    barmode overlay.

    :param fig: Figure to modify in place
    :type fig: go.Figure
    :param width: Width of each bar, in axis units
    :type width: float
    """

    def overlay(trace, color, w, offset):
        t = copy.deepcopy(trace)
        t.update(
            marker=dict(color=color, line=dict(width=0), cornerradius=4),
            width=w,
            offset=offset,
            hoverinfo="skip",
            hovertemplate=None,
            showlegend=False,
            text=None,
            name="",
        )
        return t

    base = -width / 2
    bodies = [t for t in fig.data if isinstance(t, go.Bar)]
    shadows, glosses = [], []

    for trace in bodies:
        trace.update(
            width=width,
            offset=base,
            opacity=1,
            marker=dict(color=trace.marker.color, line=dict(color="rgba(0,0,0,0.35)", width=1), cornerradius=4),
            # Simple bubble: white background, black text, outline matching the bar
            hoverlabel=dict(bgcolor="#ffffff", bordercolor=trace.marker.color,
                            font=dict(family=FONT, size=13, color="#000000")),
        )

        # Drop shadow - slightly offset from the bar
        shadows.append(overlay(trace, "rgba(15,29,51,0.22)", width, base + 0.14 * width))

        # Depth - dark band over the trailing third
        glosses.append(overlay(trace, "rgba(0,0,0,0.16)", width * 0.38, base + width * 0.62))

        # Gloss - light band over the leading half
        glosses.append(overlay(trace, "rgba(255,255,255,0.34)", width * 0.42, base + width * 0.04))

    # Add the overlays, then reorder so that shadows draw first and gloss last
    for t in shadows + glosses:
        fig.add_trace(t)

    n = len(bodies)
    originals = list(fig.data[:n])
    new_shadows = list(fig.data[n:n + len(shadows)])
    new_glosses = list(fig.data[n + len(shadows):])
    fig.data = tuple(new_shadows + originals + new_glosses)

def style_axes(fig : go.Figure) -> None:
    """
    Apply the common look (fonts, gridlines, background) to a figure

    :param fig: Figure to modify in place
    :type fig: go.Figure
    """

    fig.update_layout(
        font=dict(family=FONT, size=13, color="#1c2433"),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#f6f8fc",
        hoverlabel=dict(bgcolor="#ffffff", font=dict(family=FONT, size=13, color="#000000"), align="left"),
    )
    fig.update_xaxes(gridcolor="#dfe5f0", gridwidth=1, linecolor="#b7c2d6", zeroline=False)
    fig.update_yaxes(gridcolor="#e8ecf4", gridwidth=1, linecolor="#b7c2d6", zeroline=False)

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
    df_new = df.fillna(value={"end": default_end_date})
    default_end = max(df_new[x_end[0]].max(), default_end_date)
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

    fig = px.timeline(
        df_new,
        custom_data=[y[0], "_start", "_end", "_desc", "_opacity"],
        title=title,
        x_start=x_start[0],
        x_end=x_end[0],
        y=y[0],
        color=y[0],
        color_discrete_map=colors,
        labels ={x_start[0] : x_start[1],
                 x_end[0] : x_end[1],
                 y[0] : y[1]}
    )

    fig.update_traces(
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} to %{customdata[2]}"
                      "<br>%{customdata[3]}<extra></extra>"
    )

    if link_key is not None:
        fig.update_layout(meta={"link_key": link_key})

    rows = 1
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
                fig.add_vline(
                    x=first.timestamp()*1000,
                    line_width=2,
                    line_dash="dash",
                    line_color="#d62839",
                    annotation_text=k,
                    annotation_position="top right",
                    annotation_yshift=20 + row * MARKER_ROW_HEIGHT,
                    annotation_font=dict(color="#d62839", size=12)
                )
                continue

            # Window: dotted line at each end, joined by a horizontal line above the plot
            top = 1 + (20 + row * MARKER_ROW_HEIGHT) / max(plot_height, 1)
            line = dict(color="#d62839", width=2, dash="dot")
            for x in (first, last):
                fig.add_shape(type="line", xref="x", yref="paper", x0=x, x1=x, y0=0, y1=top, line=line)
            fig.add_shape(type="line", xref="x", yref="paper", x0=first, x1=last, y0=top, y1=top,
                          line=dict(color="#d62839", width=2))
            fig.add_annotation(xref="x", yref="paper", x=first, y=top, text=k, showarrow=False,
                               xanchor="left", yanchor="bottom", xshift=4,
                               font=dict(color="#d62839", size=12))
        rows = max(len(row_ends), 1)

    # Opacity of each bar, set before shading so the shading is faded with the bar
    if opacity is not None:
        for trace in fig.data:
            if isinstance(trace, go.Bar) and trace.customdata is not None:
                trace.marker.opacity = [float(cd[4]) for cd in trace.customdata]

    style_axes(fig)
    _shade_bars(fig, BAR_WIDTH)

    # Milestone each row is working towards
    if milestones is not None and milestones[0] in df_new.columns and milestones[1] in df_new.columns:
        ms = df_new[df_new[milestones[1]].notna()]
        if not ms.empty:
            fig.add_trace(go.Scatter(
                x=ms[milestones[1]],
                y=ms[y[0]],
                mode="markers",
                marker=dict(symbol="diamond", size=16, color="#d62839", line=dict(color="white", width=1.5)),
                customdata=ms[[milestones[0], milestones[1]]].assign(**{milestones[1] : ms[milestones[1]].dt.strftime("%Y-%m-%d")}).to_numpy(),
                hovertemplate="<b>%{y}</b><br>Milestone %{customdata[0]}: %{customdata[1]}<extra></extra>",
                showlegend=False,
            ))

    fig.update_layout(
        barmode="overlay",
        xaxis_title=f"{x_start[1]} - {x_end[1]}",
        yaxis_title=f"{y[1]}",
        showlegend=show_legend,
        legend=LEGEND_OUTSIDE | dict(title_text=y[1]),
        title= {'x':0.5, 'xanchor': 'center', 'yanchor': 'top'},
        margin=(dict(l=50, r=50, t=50 + (rows - 1) * MARKER_ROW_HEIGHT, b=50)),
        colorway=px.colors.qualitative.Alphabet,
        height=((n_rows*bar_height) + 100 + (rows - 1) * MARKER_ROW_HEIGHT),
        autosize=True,
    )

    # Choose a tick spacing so labels stay readable whatever the date range
    span_days = (df_new[x_end[0]].max() - df_new[x_start[0]].min()).days
    if span_days < 3650:
        dtick, tickformat = "M3", "%b\n%Y"
    else:
        dtick, tickformat = "M12", "%Y"

    fig.update_xaxes(
        dtick=dtick,
        tickformat=tickformat,
        ticklabelmode="period",
        tickangle=0,
        automargin=True
    )

    # Tell the html page to offer a scale select box for the ticks
    meta = dict(fig.layout.meta or {})
    meta["scale_ticks"] = True
    meta["scale_default"] = "Quarterly" if dtick == "M3" else "Yearly"
    fig.update_layout(meta=meta)

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

    # Create the Plotly Stacked Bar Chart
    fig = px.bar(
        df,
        title=title,
        x=x[0],
        y=y[0],
        color=color,
        color_discrete_map=colors,
        category_orders={color: list(colors)} if colors else None,
        labels={x[0]: x[1], y[0]: y[1]},
        barmode='stack'
    )

    style_axes(fig)

    # Plotly cannot layer overlays on a stacked bar, so stack by hand:
    # give every bar an explicit base and draw in overlay mode
    totals = {}
    for trace in fig.data:
        bases = []
        for xv, yv in zip(trace.x, trace.y, strict=True):
            bases.append(totals.get(xv, 0))
            totals[xv] = totals.get(xv, 0) + (yv or 0)
        trace.base = bases

    # Bar width in axis units (milliseconds for dates)
    xs = pd.Series(df[x[0]].unique()).sort_values()
    if pd.api.types.is_datetime64_any_dtype(xs):
        gap = xs.diff().min()
        width = (gap if pd.notna(gap) else pd.Timedelta(days=30)).total_seconds() * 1000 * 0.7
    else:
        width = 0.7

    fig.update_layout(barmode="overlay")

    # Hover text, built explicitly so it is always populated
    descriptions = descriptions or {}
    for trace in fig.data:
        trace.customdata = [[descriptions.get(trace.name, "")]] * len(trace.x)
    fig.update_traces(
        hovertemplate=f"<b>%{{fullData.name}}</b><br>{x[1]}: %{{x|{hover_date_format}}}"
                      f"<br>{y[1]}: %{{y:.4~g}}<br>%{{customdata[0]}}<extra></extra>"
    )

    if link_key is not None:
        fig.update_layout(meta={"link_key": link_key, "link_by": "trace"})
    if link_to is not None:
        fig.update_layout(meta={"link_key": link_to[0], "link_to": link_to[1]})

    _shade_bars(fig, width)

    # Clean up the X-Axis formatting
    fig.update_xaxes(
        tickmode="array",
        tickvals=df[x[0]].unique(),
        tickangle=-45
    )
    if tickformat is not None:
        fig.update_xaxes(tickformat=tickformat)

    # Fill the card, unless the bars need more room than it has, in which case the chart scrolls
    plot_width = bar_width * len(df[x[0]].unique())
    if plot_width > MAX_PLOT_WIDTH:
        fig.update_layout(width=plot_width + 200 + (LEGEND_WIDTH if legend_outside else 0), autosize=False)
    else:
        fig.update_layout(autosize=True)

    # Update layout
    fig.update_layout(
        height=height,
        legend_title_text=color.split(".")[-1].replace("_", " ").title(),
        margin=(dict(l=50, r=50, t=50, b=50)),
        colorway=px.colors.qualitative.Alphabet,
        legend=LEGEND_OUTSIDE if legend_outside else dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#b7c2d6",
            borderwidth=1
        ),
    )

    return fig

__all__ = [
    "gantt",
    "stacked_bar"
]
