import pandas as pd
import plotly.express as px
from pathlib import Path

from ._containers import Container
from ._charts import gantt, stacked_bar
from ._utils import smart_date_converter, today

class Workpackage(Container):

    def __init__(self, name : str, path : Path) -> None:
        """
        Constructor

        :param name: Name of container
        :type name: str
        :param path: Path to container
        :type path: Path
        :return: None
        """
        super().__init__("workpackage", name, path)

    def export_html(self) -> None:
        """
        Export html file

        :return: None
        """
        # Add Timeline to html
        tab = self.html.add_tab("Timelines")
        tab.add_chart("Workpackage Timelines", gantt(
                                                        self.summary_df,
                                                        "",
                                                        ("start", "Start Date"),
                                                        ("end", "End Date"),
                                                        ("workpackage", "Workpackage Name"),
                                                        markers={"Today" : today},
                                                    )
        )

        # Add Resource allocation stacked bar to html
        tab = self.html.add_tab("Allocations")
        tab.add_chart("Workpackage Allocations", create_allocation_chart(self.imported_df, "allocations.resource"))

        # Add table to html
        tab = self.html.add_tab("Workpackages")
        tab.add_table("Workpackages", self.summary_df)

        super().export_html()

class WorkPackages(Container):

    def __init__(self, name : str, path : Path) -> None:
        """
        Constructor

        :param name: Name of container
        :type name: str
        :param path: Path to container
        :type path: Path
        :return: None
        """
        super().__init__("workpackages", name, path)

    def import_data(self, l : list[dict]) -> None:
        """
        Import data from a list of dictionaries

        :param l: List of dictionaries
        :return: None
        """

        all_top_level_keys = {key for d in l for key in d.keys()}
        meta_cols = [k for k in all_top_level_keys if k != "allocations"]

        # Convert new data to dataframe
        self.imported_df = pd.json_normalize(
                                                l,
                                                record_path=["allocations"],
                                                meta=meta_cols,
                                                record_prefix="allocations.",
                                                errors="ignore"
        )

        # Columns with lists
        columns_with_lists = [
            col for col in self.imported_df.columns if self.imported_df[col].dropna().apply(lambda x: isinstance(x, list)).any()
        ]

        for col in columns_with_lists:
            self.imported_df = self.imported_df.explode(col)

        # Create a summary dataframe
        columns=[
                    "workpackage",
                    "project",
                    "allocations.start",
                    "allocations.end",
                    "allocations.resource",
                    "allocations.allocation",
                    "description"
                ]
        df = pd.DataFrame(columns=columns)
        self.validate_data(self.imported_df, df)
        df = pd.concat([self.imported_df, df], ignore_index=True)
        df = df[columns]
        self.summary_df = summarize_df(df)

        # Create child projects
        for p in l:
            name = p["workpackage"]
            if name not in self.children:
                self.children[name] = Workpackage(name, self.path)
                self.children[name].imported_df = self.imported_df[self.imported_df["workpackage"] == name]
                self.children[name].summary_df = self.summary_df[self.summary_df["workpackage"] == name]
            else:
                raise ValueError(f"milestone {name} already exists")

    def export_html(self) -> None:
        """
        Export html file

        :return: None
        """

        # Add Timeline to html
        tab = self.html.add_tab("Timelines")
        tab.add_chart("Workpackage Timelines", gantt(
                                                        self.summary_df,
                                                        "",
                                                        ("start", "Start Date"),
                                                        ("end", "End Date"),
                                                        ("workpackage", "Workpackage Name"),
                                                        markers={"Today" : today},
                                                    )
        )

        # Add Resource allocation stacked bar to html
        tab = self.html.add_tab("Allocations")
        tab.add_chart("Workpackage Allocations", create_allocation_chart(self.imported_df, "workpackage"))

        # Add table to html
        tab = self.html.add_tab("Workpackages")
        tab.add_table("Workpackages", self.summary_df)

        super().export_html()

def summarize_df(df : pd.DataFrame) -> pd.DataFrame:
    """
    Create a summarized dataframe

    :param df: Dataframe to summarize
    :type df: pd.DataFrame
    :return: pd.DataFrame
    :rtype: pd.DataFrame
    """

    # Define the aggregation rules
    agg_rules = {
        'allocations.start': 'min',
        'allocations.end': 'max',
        'allocations.resource': lambda x: list(set(x)),
        'allocations.allocation': 'sum',
        'description': 'first'
    }

    # Group and apply
    df_reduced = df.groupby(['workpackage', 'project'], as_index=False).agg(agg_rules)

    # Rename columns to your desired output names
    df_reduced = df_reduced.rename(columns={
        'allocations.start': 'start',
        'allocations.end': 'end',
        'allocations.resource': 'resources',
        'allocations.allocation': 'effort'
    })
    df_reduced["start"] = df_reduced["start"].apply(smart_date_converter)
    df_reduced["end"] = df_reduced["end"].apply(smart_date_converter)

    return df_reduced

def create_allocation_chart(df : pd.DataFrame, groupby : str) -> px.bar:
    """
    Create a stacked bar for allocations

    :param df: Dataframe to create chart from
    :type df: pd.DataFrame
    :return: px.bar
    :rtype: px.bar
    """

    # Function to return a list of month starts and ends
    def get_month_range(row):
        # 1. Convert to Timestamp if they aren't already
        start_dt = pd.to_datetime(row['allocations.start'])
        end_dt = pd.to_datetime(row['allocations.end'])

        # 2. Subtract 2 months from start, add 2 months to end
        # We use MonthBegin (MS) to ensure we hit the start of those padded months
        padded_start = start_dt - pd.DateOffset(months=2)
        padded_end = end_dt + pd.DateOffset(months=2)

        return pd.date_range(
            start=padded_start,
            end=padded_end,
            freq='MS',
            inclusive='both'
        )

    # Create a month column and explode it based on allocation start-end
    df = df.copy()
    df['month'] = df.apply(get_month_range, axis=1)
    df_monthly = df.explode('month')

    # Zero out values not within range
    mask = (df_monthly['month'] < pd.to_datetime(df_monthly['allocations.start'])) | (df_monthly['month'] > pd.to_datetime(df_monthly['allocations.end']))
    df_monthly.loc[mask, 'allocations.allocation'] = 0

    # Group by month and name to ensure overlapping entries are summed
    df_plot = df_monthly.groupby(['month', groupby], as_index=False)['allocations.allocation'].sum()

    # Create the Plotly Stacked Bar Chart
    fig = stacked_bar(
        df_plot,
        "",
        ("month", "Month"),
        ("allocations.allocation", "Allocation (Months Effort)"),
        groupby,
        height=1000,
        bar_width=50,
    )

    return fig

__all__ = [
    "WorkPackage",
    "WorkPackages",
    "summarize_df",
    "create_allocation_chart",
]
