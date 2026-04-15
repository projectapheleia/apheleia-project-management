import pandas as pd
import plotly.express as px
from pathlib import Path
import numpy as np

from ._charts import gantt, stacked_bar
from ._containers import Container
from ._utils import smart_date_converter, today

class Task(Container):

    def __init__(self, name : str, path : Path) -> None:
        """
        Constructor

        :param name: Name of container
        :type name: str
        :param path: Path to container
        :type path: Path
        :return: None
        """
        super().__init__("task", name, path)

    def export_html(self) -> None:
        """
        Export html file

        :return: None
        """
        columns=[
                    "task",
                    "project",
                    "workpackage",
                    "resource",
                    "status.date",
                    "status.spent",
                    "status.remaining",
                    "description"
                ]


        tab = self.html.add_tab("Summary")

        # Timeline
        tab.add_chart("Task Timeline", create_task_timeline(self.imported_df))

        # Summary Table
        df = self.imported_df.loc[[self.imported_df['status.date'].idxmax()]]
        df = df[columns]
        tab.add_table("", df)

        # Progress Chart
        tab = self.html.add_tab("Progress")
        tab.add_chart("Task Progress", create_task_progress(self.imported_df, "task"))

        super().export_html()

class Tasks(Container):

    def __init__(self, name : str, path : Path) -> None:
        """
        Constructor

        :param name: Name of container
        :type name: str
        :param path: Path to container
        :type path: Path
        :return: None
        """
        super().__init__("tasks", name, path)

    def import_data(self, l : list[dict]) -> None:
        """
        Import data from a list of dictionaries

        :param l: List of dictionaries
        :return: None
        """

        all_top_level_keys = {key for d in l for key in d.keys()}
        meta_cols = [k for k in all_top_level_keys if k != "status"]

        # Convert new data to dataframe
        self.imported_df = pd.json_normalize(
                                                l,
                                                record_path=["status"],
                                                meta=meta_cols,
                                                record_prefix="status.",
                                                errors="ignore"
        )
        self.imported_df["status.date"] = self.imported_df["status.date"].apply(smart_date_converter)

        # Columns with lists
        columns_with_lists = [
            col for col in self.imported_df.columns if self.imported_df[col].dropna().apply(lambda x: isinstance(x, list)).any()
        ]

        for col in columns_with_lists:
            self.imported_df = self.imported_df.explode(col)

        # Create a summary dataframe
        columns=[
                    "task",
                    "project",
                    "workpackage",
                    "resource",
                    "status.date",
                    "status.spent",
                    "status.remaining",
                    "description"
                ]
        df = pd.DataFrame(columns=columns)
        self.validate_data(self.imported_df, df)
        df = pd.concat([self.imported_df, df], ignore_index=True)
        df = df[columns]

        # Create child projects
        for p in l:
            name = p["task"]
            if name not in self.children:
                self.children[name] = Task(name, self.path)
                self.children[name].imported_df = self.imported_df[self.imported_df["task"] == name]
            else:
                raise ValueError(f"milestone {name} already exists")

    def export_html(self) -> None:
        """
        Export html file

        :return: None
        """


        tab = self.html.add_tab("Summary")

        # Timeline
        tab.add_chart("Task Timeline", create_task_timeline(self.imported_df))

        # Summary Table
        df = pd.DataFrame(columns=["task", "project", "workpackage", "resource", "description"])
        df = pd.concat([self.imported_df.reindex(columns=df.columns), df], ignore_index=True)
        df = df.drop_duplicates()
        df = df.reset_index(drop=True)
        tab.add_table("Tasks", df)

        # Progress
        tab = self.html.add_tab("Progress")
        tab.add_chart("Task Progress", create_task_progress(self.imported_df, "task"))


        super().export_html()

def create_task_timeline(df: pd.DataFrame, markers=None) -> px.timeline:
    """
    Create a timeline chart from a dataframe

    :param df: Dataframe
    :type df: pd.DataFrame
    :param markers: Markers to add to the chart
    :type markers: dict
    :return: Timeline chart
    :rtype: px.timeline
    """

    # 1. Get start and end date for task
    df = df.sort_values("status.date").groupby("task").agg(
                                                            start=("status.date", "first"),
                                                            last_status_date=("status.date", "last"),
                                                            remaining_days=("status.remaining", "last"),
                                                        ).reset_index()

    # 2. If task isn't complete and today is > last status update the last status date
    df["last_status_date"] = np.where(
                                        df["remaining_days"] != 0,
                                        df["last_status_date"].clip(lower=today),
                                        df["last_status_date"]
    )

    # 3. Calculate end date based on last status and remaining work
    df["end"] = df.apply(
                            lambda row: row["last_status_date"] + pd.offsets.BusinessDay(n=int(row["remaining_days"])),
                            axis=1
    )

    # 4. Create the chart
    fig = gantt(
                                            df,
                                            "",
                                            ("start", "Start Date"),
                                            ("end", "End Date"),
                                            ("task", "Task Name"),
                                            markers=markers,
                                        )

    return fig

def create_task_progress(df : pd.DataFrame, groupby : str) -> px.bar:
    """
    Create a stacked bar for allocations

    :param df: Dataframe to create chart from
    :type df: pd.DataFrame
    :param groupby: Column to group by
    :type groupby: str
    :return: px.bar
    :rtype: px.bar
    """

    # 1. Calculate boundaries
    start_date = df['status.date'].min() - pd.DateOffset(weeks=2)
    end_date = df['status.date'].max() + pd.DateOffset(weeks=2)

    # 2. Create the full weekly range
    full_range = pd.date_range(start=start_date, end=end_date, freq='W-MON')

    # 3. Pivot and Align
    pivot_df = df.groupby(['status.date', groupby])[['status.spent', 'status.remaining']].sum().unstack(groupby)

    # 4. Reindex to the expanded range and Forward Fill
    # This adds the 2 weeks before and 2 weeks after
    combined_index = pivot_df.index.union(full_range).sort_values()
    expanded_df = pivot_df.reindex(combined_index)
    normalized_df = expanded_df.ffill().reindex(full_range).fillna(0)

    # 5. Collapse and Melt for the chart
    project_totals = normalized_df.T.groupby(level=0).sum().T.reset_index()
    df_melted = project_totals.melt(
                                    id_vars=["index"],
                                    value_vars=["status.spent", "status.remaining"],
                                    var_name="Type",
                                    value_name="Effort"
    )

    # 6. Create Chart
    fig = stacked_bar(
                        df_melted,
                        "",
                        ("index", "Date"),
                        ("Effort", "Effort (Days)"),
                        "Type",
                        height=1000,
                        bar_width=5,
                    )

    return fig

__all__ = [
    "Task",
    "Tasks",
    "create_task_timeline",
    "create_task_progress",
]
