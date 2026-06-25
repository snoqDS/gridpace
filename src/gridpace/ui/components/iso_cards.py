"""
ISO price cards component for GridPace dashboard.
Displays current LMP, min, max, renewable penetration, and anomaly status per ISO.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from gridpace.config import app_config

STATUS_EMOJI = {
    "grey": "⚪",
    "green": "🟢",
    "yellow": "🟡",
    "red": "🔴",
    "critical": "🚨",
}

STATUS_LABEL = {
    "grey": "Insufficient data",
    "green": "Normal",
    "yellow": "Elevated",
    "red": "Anomalous",
    "critical": "Critical",
}


def lmp_color(avg_lmp: float) -> str:
    """
    Return a Streamlit metric color hint based on LMP price level.
    Thresholds sourced from config/settings.yml under thresholds.lmp.
    Static display bands only — see anomaly module for statistical baselines.
    """
    normal_max = app_config["thresholds"]["lmp"]["normal_max"]
    elevated_max = app_config["thresholds"]["lmp"]["elevated_max"]
    if avg_lmp < normal_max:
        return "normal"
    elif avg_lmp < elevated_max:
        return "off"
    else:
        return "inverse"


def render_fuel_mix_donut(iso_data: pd.Series, iso: str) -> None:
    """
    Render a donut chart showing fuel mix breakdown for one ISO.
    """
    fuels = ["natural_gas", "wind", "solar", "coal", "nuclear", "other"]
    labels = ["Natural Gas", "Wind", "Solar", "Coal", "Nuclear", "Other"]
    colors = ["#f4a261", "#56cfe1", "#f9c74f", "#6d6875", "#80b918", "#adb5bd"]

    values = []
    plot_labels = []
    plot_colors = []

    for fuel, label, color in zip(fuels, labels, colors, strict=True):
        val = iso_data.get(fuel)
        if val is not None and val > 1.0:
            values.append(round(val, 1))
            plot_labels.append(label)
            plot_colors.append(color)

    if not values:
        st.caption("No fuel mix data available.")
        return

    fig = go.Figure(go.Pie(
        labels=plot_labels,
        values=values,
        hole=0.5,
        marker=dict(colors=plot_colors),
        textinfo="percent",
        textfont=dict(size=9),
        hovertemplate="%{label}: %{value:.1f}%<extra></extra>",
        showlegend=True,
        title=dict(text=iso, font=dict(size=11, color="white")),
    ))

    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=250,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.4,
            xanchor="center",
            x=0.5,
            font=dict(size=9),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
    )

    st.plotly_chart(fig, use_container_width=True)


def render_iso_cards(df: pd.DataFrame, anomaly_results: dict = None) -> None:
    """
    Render LMP price cards for each ISO in a row.

    Args:
        df: gold.iso_summary DataFrame with one row per ISO
        anomaly_results: dict from detect_anomalies(), keyed by ISO
    """
    if df is None or df.empty:
        st.info("No grid data available yet. Run the pipeline to collect data.")
        st.caption("Steps to populate data:")
        st.markdown("""
        1. Set `dry_run: true` in `config/settings.yml` (uses sample data, no API calls)
        2. Run the pipeline: `uv run python -m gridpace.grid.flows`
        3. Refresh this page

        To use live data, set `dry_run: false` — note this consumes API quota.
        """)
        return

    if anomaly_results is None:
        anomaly_results = {}

    isos = df["iso"].unique()
    cols = st.columns(len(isos))

    for col, iso in zip(cols, isos, strict=True):
        iso_data = df[df["iso"] == iso].iloc[0]
        anomaly = anomaly_results.get(iso, {})
        status = anomaly.get("status", "grey")
        z_score = anomaly.get("z_score")

        with col:
            # Status indicator
            emoji = STATUS_EMOJI.get(status, "⚪")
            label = STATUS_LABEL.get(status, "Unknown")
            st.subheader(f"{emoji} {iso}")
            st.caption(f"Status: {label}" + (f" (z={z_score:.2f})" if z_score is not None else ""))

            st.metric(
                label="Avg LMP ($/MWh)",
                value=f"${iso_data['avg_lmp']:.2f}",
            )

            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="Min", value=f"${iso_data['min_lmp']:.2f}")
            with col2:
                st.metric(label="Max", value=f"${iso_data['max_lmp']:.2f}")

            renewable = iso_data.get("renewable_pct")
            if renewable is not None:
                st.metric(label="Renewable %", value=f"{renewable:.1f}%")

            st.divider()

            # Time frame context
            window_end = iso_data.get("window_end")
            if window_end is not None:
                lookback = app_config["dashboard"]["lookback_hours"]
                st.caption(f"Last {lookback}h ending {pd.Timestamp(window_end).strftime('%Y-%m-%d %H:%M UTC')}")   
            # Fuel mix donut
            render_fuel_mix_donut(iso_data, iso)

            st.divider()
