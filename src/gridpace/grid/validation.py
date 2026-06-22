"""
Data contract validation for GridPace.
Validates DataFrames against YAML schema contracts before silver layer promotion.
Contracts defined in src/gridpace/grid/contracts/
"""

from pathlib import Path

import pandas as pd
import yaml

CONTRACTS_DIR = Path(__file__).parent / "contracts"


def load_contract(source: str, dataset: str) -> dict:
    """
    Load a dataset contract from a YAML file.

    Args:
        source: data source name e.g. 'gridstatus'
        dataset: dataset name e.g. 'lmp' or 'fuel_mix'

    Returns:
        dict of field definitions from the contract
    """
    contract_path = CONTRACTS_DIR / f"{source}.yml"

    if not contract_path.exists():
        raise FileNotFoundError(f"Contract not found: {contract_path}")

    with open(contract_path) as f:
        contract = yaml.safe_load(f)

    datasets = contract.get("datasets", {})
    if dataset not in datasets:
        raise KeyError(f"Dataset '{dataset}' not found in contract '{source}.yml'")

    return datasets[dataset]["fields"]

def _check_type(series: pd.Series, expected_type: str, field_name: str) -> list:
    """
    Check if a pandas Series matches the expected contract type.
    Returns list of error strings — empty if no errors.

    Supported types: string, float, int, datetime, bool
    """
    errors = []
    # Skip type check if series is all null
    if series.isna().all():
        return errors

    type_checks = {
        "string": lambda s: pd.api.types.is_string_dtype(s) or pd.api.types.is_object_dtype(s),
        "float": lambda s: pd.api.types.is_float_dtype(s) or pd.api.types.is_numeric_dtype(s),
        "int": lambda s: pd.api.types.is_integer_dtype(s),
        "datetime": lambda s: pd.api.types.is_datetime64_any_dtype(s) or pd.api.types.is_object_dtype(s),
        "bool": lambda s: pd.api.types.is_bool_dtype(s),
    }

    if expected_type not in type_checks:
        errors.append(f"Unknown type '{expected_type}' in contract for field '{field_name}'")
        return errors

    if not type_checks[expected_type](series):
        actual_type = str(series.dtype)
        errors.append(
            f"Field '{field_name}' expected type '{expected_type}' but got '{actual_type}'"
        )

    return errors

def validate_dataframe(
    df: pd.DataFrame,
    source: str,
    dataset: str,
) -> dict:
    """
    Validate a DataFrame against a data contract.

    Args:
        df: DataFrame to validate
        source: data source name e.g. 'gridstatus'
        dataset: dataset name e.g. 'lmp' or 'fuel_mix'

    Returns:
        dict with keys:
            valid: bool — True if all checks passed
            errors: list of error message strings
            warnings: list of warning message strings
            rows_checked: int
            rows_failed: int
    """
    fields = load_contract(source, dataset)
    errors = []
    warnings = []

    for field in fields:
        name = field["name"]
        expected_type = field["type"]
        nullable = field.get("nullable", True)

        # Check field existence
        if name not in df.columns:
            if not nullable:
                errors.append(f"Required field '{name}' is missing from DataFrame")
            else:
                warnings.append(f"Optional field '{name}' is missing from DataFrame")
            continue

        # Check nullability
        null_count = df[name].isna().sum()
        if null_count > 0 and not nullable:
            errors.append(
                f"Field '{name}' has {null_count} null values but is required non-null"
            )

        # Check type
        type_errors = _check_type(df[name], expected_type, name)
        errors.extend(type_errors)

    rows_failed = len(df) if errors else 0

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "rows_checked": len(df),
        "rows_failed": rows_failed,
    }
