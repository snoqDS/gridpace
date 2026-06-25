"""
Statistical anomaly detection for GridPace.
Computes z-score based baselines per ISO from gold layer history.
Flags sustained conditions only — not transient price spikes.

Polling resolution constraint: 2-hour intervals miss short spikes.
Anomaly detection is designed for sustained conditions only.
See docs/architecture.md for full constraint documentation.
"""

import pandas as pd

from gridpace.config import app_config
from gridpace.monitoring.logger import get_logger

log = get_logger(__name__)

# Anomaly detection thresholds — sourced from config/settings.yml [anomaly]
# Defaults mirror settings.yml values; config is the authoritative source.
_anomaly_cfg = app_config.get("anomaly", {})

MIN_DATA_POINTS: int = _anomaly_cfg.get("min_data_points", 5)
Z_ELEVATED: float = _anomaly_cfg.get("z_score_elevated", 1.0)   # yellow
Z_HIGH: float = _anomaly_cfg.get("z_score_high", 2.0)           # red
Z_CRITICAL: float = _anomaly_cfg.get("z_score_critical", 3.0)   # critical


def compute_iso_baseline(df: pd.DataFrame, iso: str) -> dict | None:
    """
    Compute statistical baseline for a single ISO from gold layer history.

    Args:
        df: gold.iso_summary DataFrame with full history for one ISO
        iso: ISO name e.g. 'ERCOT'

    Returns:
        dict with mean, std, count — or None if insufficient data
    """
    iso_df = df[df["iso"] == iso]["avg_lmp"].dropna()

    if len(iso_df) < MIN_DATA_POINTS:
        log.info(
            "insufficient_data_for_baseline",
            iso=iso,
            count=len(iso_df),
            required=MIN_DATA_POINTS,
        )
        return None

    return {
        "mean": iso_df.mean(),
        "std": iso_df.std(),
        "count": len(iso_df),
        "q25": iso_df.quantile(0.25),
        "q75": iso_df.quantile(0.75),
        "spread": iso_df.quantile(0.75) - iso_df.quantile(0.25),
    }


def compute_z_score(value: float, baseline: dict) -> float | None:
    """
    Compute z-score for a value against a baseline.
    Returns None if std is zero (all values identical).
    """
    if baseline["std"] == 0:
        return None
    return (value - baseline["mean"]) / baseline["std"]


def get_anomaly_status(z_score: float | None) -> str:
    """
    Map z-score to a five-level traffic light status.

    Thresholds are loaded from config/settings.yml [anomaly] at startup.
    Default breakpoints align with standard normal distribution coverage:
        z < 1.0  => ~68% of observations are within this band (normal)
        z < 2.0  => ~95% coverage (elevated)
        z < 3.0  => ~99.7% coverage (high anomaly)
        z >= 3.0 => extreme outlier (critical)

    Returns:
        'grey'     — insufficient history to compute baseline
        'green'    — normal    (|z| < Z_ELEVATED)
        'yellow'   — elevated  (Z_ELEVATED <= |z| < Z_HIGH)
        'red'      — anomalous (Z_HIGH <= |z| < Z_CRITICAL)
        'critical' — extreme   (|z| >= Z_CRITICAL)
    """
    if z_score is None:
        return "grey"
    abs_z = abs(z_score)
    if abs_z < Z_ELEVATED:
        return "green"
    elif abs_z < Z_HIGH:
        return "yellow"
    elif abs_z < Z_CRITICAL:
        return "red"
    else:
        return "critical"


def detect_anomalies(history_df: pd.DataFrame, current_df: pd.DataFrame) -> dict:
    """
    Detect anomalies for all ISOs.

    Args:
        history_df: full gold.iso_summary history
        current_df: latest gold.iso_summary snapshot (one row per ISO)

    Returns:
        dict keyed by ISO with status, z_score, baseline, and current value
    """
    results = {}
    isos = current_df["iso"].unique()

    for iso in isos:
        baseline = compute_iso_baseline(history_df, iso)
        current_row = current_df[current_df["iso"] == iso]

        if current_row.empty:
            results[iso] = {"status": "grey", "reason": "no current data"}
            continue

        current_lmp = current_row["avg_lmp"].iloc[0]

        if baseline is None:
            results[iso] = {
                "status": "grey",
                "reason": f"insufficient data (need {MIN_DATA_POINTS} points)",
                "current_lmp": current_lmp,
                "z_score": None,
                "baseline": None,
            }
            continue

        z_score = compute_z_score(current_lmp, baseline)
        status = get_anomaly_status(z_score)

        results[iso] = {
            "status": status,
            "current_lmp": current_lmp,
            "z_score": round(z_score, 2) if z_score is not None else None,
            "baseline": baseline,
            "reason": f"z_score={z_score:.2f}" if z_score is not None else "std=0",
        }

        log.info(
            "anomaly_detection_result",
            iso=iso,
            status=status,
            current_lmp=current_lmp,
            z_score=z_score,
        )

    return results
