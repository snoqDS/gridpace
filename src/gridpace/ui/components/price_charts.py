"""
Price distribution and generation mix charts for GridPace dashboard.
Used in the Price Analytics tab.

All charts support dynamic ISO lists — driven by app_config["isos"].
Adding a new ISO to config/settings.yml automatically appears in all charts.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Color sequence for ISOs — scales automatically with more ISOs
ISO_COLORS = {
    "ERCOT": "#56cfe1",
    "CAISO": "#f9c74f",
    "PJM": "#80b918",
    "MISO": "#f4a261",
    "SPP": "#c77dff",
    "NYISO": "#ff6b6b",
    "ISONE": "#ffd166",
}

FUEL_COLORS = {
    "natural_gas": "#f4a261",
    "wind": "#56cfe1",
    "solar": "#f9c74f",
    "coal": "#6d6875",
    "nuclear": "#80b918",
    "other": "#adb5bd",
}


def _get_iso_color(iso: str) -> str:
    """Return color for ISO, falling back to grey for unknown ISOs."""
    return ISO_COLORS.get(iso, "#adb5bd")


def render_lmp_histogram(df: pd.DataFrame) -> None:
    """
    Render overlaid LMP price histogram for all ISOs.
    Shows price frequency distribution with all ISOs on one chart.

    Args:
        df: gold.iso_summary history with iso and avg_lmp columns
    """
    if df is None or df.empty:
        st.info("No price history available.")
        return

    fig = go.Figure()

    for iso in sorted(df["iso"].unique()):
        iso_df = df[df["iso"] == iso]["avg_lmp"].dropna()
        fig.add_trace(go.Histogram(
            x=iso_df,
            name=iso,
            opacity=0.7,
            marker_color=_get_iso_color(iso),
            nbinsx=20,
            hovertemplate=f"{iso}<br>Price: $%{{x:.1f}}/MWh<br>Hours: %{{y}}<extra></extra>",
        ))

    fig.update_layout(
        barmode="group",
        title="LMP Price Distribution",
        xaxis_title="Avg LMP ($/MWh)",
        yaxis_title="Hours",
        legend_title="ISO",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        height=350,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_lmp_cdf(df: pd.DataFrame) -> None:
    """
    Render overlaid CDF of LMP prices for all ISOs.
    Shows what percentage of hours had prices below each threshold.
    Useful for battery operators identifying charging opportunity windows.

    Args:
        df: gold.iso_summary history with iso and avg_lmp columns
    """
    if df is None or df.empty:
        st.info("No price history available.")
        return

    fig = go.Figure()

    for iso in sorted(df["iso"].unique()):
        iso_prices = df[df["iso"] == iso]["avg_lmp"].dropna().sort_values()
        cdf = [i / len(iso_prices) * 100 for i in range(1, len(iso_prices) + 1)]

        fig.add_trace(go.Scatter(
            x=iso_prices.values,
            y=cdf,
            name=iso,
            mode="lines",
            line=dict(color=_get_iso_color(iso), width=2),
            hovertemplate=f"{iso}<br>Price: $%{{x:.1f}}/MWh<br>Below this: %{{y:.1f}}%<extra></extra>",
        ))

    fig.update_layout(
        title="Cumulative Distribution of LMP Prices",
        xaxis_title="Avg LMP ($/MWh)",
        yaxis_title="% of Hours Below This Price",
        legend_title="ISO",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.1)", range=[0, 100]),
        height=350,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_lmp_boxplot(df: pd.DataFrame) -> None:
    """
    Render box plots of LMP prices per ISO.
    Shows median, IQR, whiskers, and outliers for price comparison.

    Args:
        df: gold.iso_summary history with iso and avg_lmp columns
    """
    if df is None or df.empty:
        st.info("No price history available.")
        return

    fig = go.Figure()

    for iso in sorted(df["iso"].unique()):
        iso_df = df[df["iso"] == iso]["avg_lmp"].dropna()
        fig.add_trace(go.Box(
            y=iso_df,
            name=iso,
            marker_color=_get_iso_color(iso),
            boxmean=True,
            hovertemplate=f"{iso}<br>Price: $%{{y:.1f}}/MWh<extra></extra>",
        ))

    fig.update_layout(
        title="LMP Price Distribution by ISO",
        yaxis_title="Avg LMP ($/MWh)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        height=350,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_price_spread(df: pd.DataFrame) -> None:
    """
    Render price spread (Q0.75 minus Q0.25) per ISO.
    Higher spread indicates more price volatility and arbitrage opportunity.

    Args:
        df: gold.iso_summary history with iso and avg_lmp columns
    """
    if df is None or df.empty:
        st.info("No price history available.")
        return

    spreads = []
    for iso in sorted(df["iso"].unique()):
        iso_prices = df[df["iso"] == iso]["avg_lmp"].dropna()
        q25 = iso_prices.quantile(0.25)
        q75 = iso_prices.quantile(0.75)
        spreads.append({
            "iso": iso,
            "q25": round(q25, 2),
            "q75": round(q75, 2),
            "spread": round(q75 - q25, 2),
        })

    spread_df = pd.DataFrame(spreads)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=spread_df["iso"],
        y=spread_df["spread"],
        marker_color=[_get_iso_color(iso) for iso in spread_df["iso"]],
        hovertemplate="<b>%{x}</b><br>Spread: $%{y:.2f}/MWh<extra></extra>",
    ))

    fig.update_layout(
        title="Price Spread per ISO (Q0.75 minus Q0.25)",
        xaxis_title="ISO",
        yaxis_title="Spread ($/MWh)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        height=300,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Show metrics below chart
    cols = st.columns(len(spreads))
    for col, row in zip(cols, spreads, strict=True):
        with col:
            st.metric(label=f"{row['iso']} Spread ($/MWh)", value=f"${row['spread']:.2f}")
            st.caption(f"Q25: ${row['q25']:.2f}")
            st.caption(f"Q75: ${row['q75']:.2f}")


def render_generation_mix_timeseries(df: pd.DataFrame) -> None:
    """
    Render stacked bar chart of generation mix over time per ISO.
    Shows how fuel mix changes across the lookback window.
    One stacked bar chart per ISO displayed sequentially.

    Args:
        df: gold.iso_summary history with iso, window_start, and fuel columns
    """
    if df is None or df.empty:
        st.info("No generation mix history available.")
        return

    fuel_cols = ["natural_gas", "wind", "solar", "coal", "nuclear", "other"]
    fuel_labels = ["Natural Gas", "Wind", "Solar", "Coal", "Nuclear", "Other"]

    for iso in sorted(df["iso"].unique()):
        iso_df = df[df["iso"] == iso].sort_values("window_start")

        if iso_df.empty:
            continue

        fig = go.Figure()

        for fuel, label in zip(fuel_cols, fuel_labels, strict=True):
            if fuel not in iso_df.columns:
                continue
            values = iso_df[fuel].fillna(0)
            if values.sum() == 0:
                continue

            fig.add_trace(go.Bar(
                x=iso_df["window_start"],
                y=values,
                name=label,
                marker_color=FUEL_COLORS.get(fuel, "#adb5bd"),
                hovertemplate=f"{label}: %{{y:.1f}}%<extra></extra>",
            ))

        fig.update_layout(
            barmode="overlay",
            title=f"{iso} Generation Mix Over Time",
            xaxis_title="Time",
            yaxis_title="Generation Mix (%)",
            legend_title="Fuel Type",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
            height=300,
        )

        st.plotly_chart(fig, use_container_width=True)
