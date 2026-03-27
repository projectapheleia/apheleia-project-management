import pandas as pd
import plotly.express as px
from ._utils import today, default_end_date

def gantt(  df : pd.DataFrame,
            title : str,
            x_start : tuple[str, str],
            x_end : tuple[str, str],
            y: tuple[str, str],
            markers: dict[str, pd.Timestamp]=None,
            bar_height=50,
            bar_width=1000) -> px.timeline:
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
    :param bar_width: Width of the chart
    :type bar_width: int
    :return: Gantt chart
    :rtype: px.timeline
    """

    # Create a new copy of the date
    # Insert an end date (max of the default and largest in data)
    df_new = df.fillna(value={"end": default_end_date})
    default_end = max(df_new[x_end[0]].max(), default_end_date)
    df_new = df.fillna(value={"end": default_end})

    fig = px.timeline(
        df_new,
        title=title,
        x_start=x_start[0],
        x_end=x_end[0],
        y=y[0],
        color=y[0],
        labels ={x_start[0] : x_start[1],
                 x_end[0] : x_end[1],
                 y[0] : y[1]}
    )

    if markers is not None:
        for k,v in markers.items():
            fig.add_vline(
                x=v.timestamp()*1000,
                line_width=2,
                line_dash="dash",
                line_color="red",
                annotation_text=k,
                annotation_position="top right",
                annotation_yshift=20
            )

    fig.update_layout(
        xaxis_title=f"{x_start[1]} - {x_end[1]}",
        yaxis_title=f"{y[1]}",
        showlegend=False,
        title= {'x':0.5, 'xanchor': 'center', 'yanchor': 'top'},
        margin=(dict(l=50, r=50, t=50, b=50)),
        colorway=px.colors.qualitative.Alphabet,
        height=((len(df)*bar_height) + 100),
        width=(bar_width + 200)
    )

    return fig

def stacked_bar(df : pd.DataFrame,
                title : str,
                x : tuple[str, str],
                y : tuple[str, str],
                color : str,
                height=1000,
                bar_width=50) -> px.timeline:
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
        labels={x[0]: x[1], y[0]: y[1]},
        barmode='stack'
    )

    # Clean up the X-Axis formatting
    fig.update_xaxes(
        tickmode="array",
        tickvals=df[x[0]].unique(),
        tickangle=-45
    )

    # Update layout
    fig.update_layout(
        width=max(1000, (bar_width * len(df[x[0]].unique()))) + 200,
        height=height,
        autosize=False,
        margin=(dict(l=50, r=50, t=50, b=50)),
        colorway=px.colors.qualitative.Alphabet,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bordercolor="Black",
            borderwidth=1
        ),
    )

    return fig

__all__ = [
    "gantt",
    "stacked_bar"
]
