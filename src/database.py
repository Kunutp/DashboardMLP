"""
Database connection and query utilities for Water Quality Dashboard
"""

import sqlite3
import pandas as pd
import streamlit as st
from pathlib import Path
from typing import Optional, Tuple, List
import config


@st.cache_resource
def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Get SQLite connection with error handling (cached)

    Args:
        db_path: Path to database file. If None, uses config.DATABASE_PATH

    Returns:
        SQLite connection object

    Raises:
        FileNotFoundError: If database file doesn't exist
        sqlite3.Error: If database connection fails
    """
    if db_path is None:
        db_path = config.DATABASE_PATH

    db_file = Path(db_path)

    if not db_file.exists():
        raise FileNotFoundError(
            f"Database file not found: {db_path}\n"
            f"Please ensure the database file is in the data/ folder."
        )

    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        return conn
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Failed to connect to database: {e}")


@st.cache_data(ttl=3600)
def get_data_by_month(_conn, year: int, month: int) -> pd.DataFrame:
    """
    Retrieve water quality data for a specific month

    Args:
        _conn: SQLite connection (prefixed with _ to bypass caching)
        year: Year (e.g., 2025)
        month: Month (1-12)

    Returns:
        DataFrame with water quality data
    """
    month_str = f"{month:02d}"
    query = """
        SELECT *
        FROM water_quality_data
        WHERE strftime('%Y', date) = ?
          AND strftime('%m', date) = ?
        ORDER BY date, time_period, sampling_point, parameter
    """

    try:
        df = pd.read_sql_query(query, _conn, params=(str(year), month_str))
        return df
    except Exception as e:
        st.error(f"Error retrieving data: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_jar_test_by_month(_conn, year: int, month: int) -> pd.DataFrame:
    """
    Retrieve jar test results for a specific month

    Args:
        _conn: SQLite connection (prefixed with _ to bypass caching)
        year: Year (e.g., 2025)
        month: Month (1-12)

    Returns:
        DataFrame with jar test results
    """
    month_str = f"{month:02d}"
    query = """
        SELECT *
        FROM jar_test_results
        WHERE strftime('%Y', date) = ?
          AND strftime('%m', date) = ?
        ORDER BY date, time_period, jar_number
    """

    try:
        df = pd.read_sql_query(query, _conn, params=(str(year), month_str))
        return df
    except Exception as e:
        st.error(f"Error retrieving jar test data: {e}")
        return pd.DataFrame()


def get_available_months(_conn) -> List[Tuple[int, int]]:
    """
    Get list of available year-month combinations in the database

    Args:
        _conn: SQLite connection

    Returns:
        List of (year, month) tuples sorted descending
    """
    query = """
        SELECT DISTINCT
            CAST(strftime('%Y', date) AS INTEGER) as year,
            CAST(strftime('%m', date) AS INTEGER) as month
        FROM water_quality_data
        ORDER BY year DESC, month DESC
    """

    try:
        df = pd.read_sql_query(query, _conn)
        return list(zip(df['year'], df['month']))
    except Exception as e:
        st.error(f"Error retrieving available months: {e}")
        return []


def get_database_summary(_conn) -> dict:
    """
    Get summary statistics about the database

    Args:
        _conn: SQLite connection

    Returns:
        Dictionary with summary statistics
    """
    summary = {}

    try:
        # Count records in water_quality_data
        summary['water_quality_count'] = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM water_quality_data", _conn
        ).iloc[0]['count']

        # Count records in jar_test_results
        summary['jar_test_count'] = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM jar_test_results", _conn
        ).iloc[0]['count']

        # Get date range
        date_range = pd.read_sql_query(
            "SELECT MIN(date) as min_date, MAX(date) as max_date FROM water_quality_data", _conn
        ).iloc[0]
        summary['date_range'] = (date_range['min_date'], date_range['max_date'])

        # Get unique parameters
        params = pd.read_sql_query(
            "SELECT DISTINCT parameter FROM water_quality_data ORDER BY parameter", _conn
        )['parameter'].tolist()
        summary['parameters'] = params

        # Get unique sampling points
        points = pd.read_sql_query(
            "SELECT DISTINCT sampling_point FROM water_quality_data ORDER BY sampling_point", _conn
        )['sampling_point'].tolist()
        summary['sampling_points'] = points

    except Exception as e:
        st.error(f"Error retrieving database summary: {e}")

    return summary
