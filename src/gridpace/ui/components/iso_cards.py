"""
ISO price cards component for GridPace dashboard.
Displays current LMP, min, max, and renewable penetration per ISO.
"""

import pandas as pd
import streamlit as st

from gridpace.config import app_config


def lmp_color(avg_lmp: float) -> str:
    """
    Return a status color based on LMP price level.
    Thresholds configured in config/settings.yml under thresholds.lmp.
    TODO Future: replace with statistical baselines per ISO.
    """
    normal_max = app_config["thresholds"]["lmp"]["normal_max"]
    elevated_max = app_config["thresholds"]["lmp"]["elevated_max"]

    if avg_lmp < normal_max:
        return "normal"
    elif avg_lmp < elevated_max:
        return "off"
    else:
        return "inverse"

def render_iso_cards(df: pd.DataFrame) -> None:
    """
    Render LMP price cards for each ISO in a row.

    Args:
        df: gold.iso_summary DataFrame with one row per ISO
    """
    if df is None or df.empty:
        st.info("No grid data available yet. Run the pipeline to collect data.")
        st.code("uv run python -m gridpace.grid.flows")
        return

    isos = df["iso"].unique()
    cols = st.columns(len(isos))

    for col, iso in zip(cols, isos, strict=True):
        iso_data = df[df["iso"] == iso].iloc[0]

        with col:
            st.subheader(iso)

            st.metric(
                label="Avg LMP ($/MWh)",
                value=f"${iso_data['avg_lmp']:.2f}",
            )

            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    label="Min",
                    value=f"${iso_data['min_lmp']:.2f}",
                )
            with col2:
                st.metric(
                    label="Max",
                    value=f"${iso_data['max_lmp']:.2f}",
                )

            renewable = iso_data.get("renewable_pct")
            if renewable is not None:
                st.metric(
                    label="Renewable %",
                    value=f"{renewable:.1f}%",
                )

            st.divider()
