"""
Data processing logic for Water Quality Dashboard
Implements business rules: @RW<100 filtering, Jar Test counts, and statistical calculations
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import config


class WaterQualityProcessor:
    """Process water quality data according to business rules"""

    def __init__(self, df: pd.DataFrame, thresholds: Dict):
        """
        Initialize processor

        Args:
            df: Water quality DataFrame
            thresholds: Dictionary of threshold values
        """
        self.df = df.copy()
        self.thresholds = thresholds

    def apply_rw_filtering(self) -> pd.DataFrame:
        """
        Apply @RW<100 filtering logic
        Exclude FW/TW data when RW Turbidity > threshold at the same timestamp

        Returns:
            Filtered DataFrame
        """
        if self.df.empty:
            return self.df

        df_filtered = self.df.copy()
        rw_threshold = self.thresholds.get('rw_turbidity_threshold', 100.0)

        # Find time periods where RW turbidity exceeds threshold
        rw_turbidity = self.df[
            (self.df['parameter'] == 'Turbidity') &
            (self.df['sampling_point'].isin(config.SAMPLING_GROUPS['RW']))
        ]

        # Get problematic time periods
        problematic_periods = rw_turbidity[
            rw_turbidity['value'] > rw_threshold
        ][['date', 'time_period']].drop_duplicates()

        if problematic_periods.empty:
            return df_filtered

        # Filter out FW and TW data during problematic periods
        mask = (
            (~self.df['sampling_point'].isin(config.SAMPLING_GROUPS['FW'] + config.SAMPLING_GROUPS['TW'])) |
            (~self.df[['date', 'time_period']].apply(
                lambda row: any(
                    (row['date'] == period['date']) &
                    (row['time_period'] == period['time_period'])
                    for _, period in problematic_periods.iterrows()
                ), axis=1
            ))
        )

        return df_filtered[mask]

    def get_sampling_point_group(self, sampling_point: str) -> Optional[str]:
        """
        Get group name (RW, CW, FW, TW) for a sampling point

        Args:
            sampling_point: Sampling point name

        Returns:
            Group name or None
        """
        # Special case: direct group name matches (CW, FW, TW, RW)
        if sampling_point in ['RW', 'CW', 'FW', 'TW']:
            return sampling_point

        # Check in standard groups
        for group, points in config.SAMPLING_GROUPS.items():
            if sampling_point in points:
                return group
        return None

    def get_sampling_points_for_parameter(self, parameter: str, group: str) -> list:
        """
        Get appropriate sampling points for a specific parameter

        Args:
            parameter: Parameter name
            group: Group name (RW, CW, FW, TW)

        Returns:
            List of sampling points
        """
        # Check if there's a custom override for this parameter
        if parameter in config.PARAMETER_SAMPLING_POINT_OVERRIDE:
            override_map = config.PARAMETER_SAMPLING_POINT_OVERRIDE[parameter]
            if group in override_map:
                return override_map[group]

        # Default: use standard sampling groups
        return config.SAMPLING_GROUPS.get(group, [])

    def count_samples_by_group_and_parameter(self) -> pd.DataFrame:
        """
        Count samples by group and parameter
        Handles special parameters that use different sampling points

        Returns:
            DataFrame with counts per group and parameter
        """
        if self.df.empty:
            return pd.DataFrame()

        # Use original dataframe without filtering by group
        # This allows "CW", "FW", "TW" to be counted even if they're not in standard groups
        df_raw = self.df.copy()

        # Count samples manually to handle special cases
        result_data = []

        for param in df_raw['parameter'].unique():
            for group in ['RW', 'CW', 'FW', 'TW']:
                # Get appropriate sampling points for this parameter+group combination
                sampling_points = self.get_sampling_points_for_parameter(param, group)

                # Count samples for these sampling points (exclude NaN values)
                count = df_raw[
                    (df_raw['parameter'] == param) &
                    (df_raw['sampling_point'].isin(sampling_points)) &
                    (df_raw['value'].notna())  # Count only non-NaN values
                ].shape[0]

                result_data.append({
                    'parameter': param,
                    'group': group,
                    'count': count
                })

        # Create DataFrame
        counts_df = pd.DataFrame(result_data)
        if counts_df.empty:
            return pd.DataFrame()

        # Pivot to get parameters as rows, groups as columns
        counts = counts_df.pivot(index='parameter', columns='group', values='count').fillna(0)

        # Reorder columns
        for col in ['RW', 'CW', 'FW', 'TW']:
            if col not in counts.columns:
                counts[col] = 0

        counts = counts[['RW', 'CW', 'FW', 'TW']]

        return counts

    def calculate_statistics(
        self,
        sampling_points: list,
        parameter: str,
        apply_filter: bool = False
    ) -> Dict[str, float]:
        """
        Calculate statistics for specific sampling points and parameter

        Args:
            sampling_points: List of sampling points (or group name like 'TW', 'FW')
            parameter: Parameter name
            apply_filter: Whether to apply @RW<100 filtering

        Returns:
            Dictionary with mean, p95, p100
        """
        # If sampling_points is a string (group name), get appropriate points for parameter
        if isinstance(sampling_points, str):
            sampling_points = self.get_sampling_points_for_parameter(parameter, sampling_points)

        df_to_use = self.apply_rw_filtering() if apply_filter else self.df

        filtered = df_to_use[
            (df_to_use['sampling_point'].isin(sampling_points)) &
            (df_to_use['parameter'] == parameter) &
            (df_to_use['value'].notna())
        ]['value']

        if filtered.empty:
            return {'mean': np.nan, 'p95': np.nan, 'p100': np.nan}

        return {
            'mean': filtered.mean(),
            'p95': filtered.quantile(0.95),
            'p100': filtered.max()
        }

    def count_nc_samples(
        self,
        sampling_points: list,
        parameter: str,
        condition: callable
    ) -> Tuple[int, int]:
        """
        Count NC (Non-Compliance) samples

        Args:
            sampling_points: List of sampling points (or group name like 'TW')
            parameter: Parameter name
            condition: Function that takes value and returns True if NC

        Returns:
            Tuple of (nc_count, total_count)
        """
        # If sampling_points is a string (group name), get appropriate points for parameter
        if isinstance(sampling_points, str):
            sampling_points = self.get_sampling_points_for_parameter(parameter, sampling_points)

        filtered = self.df[
            (self.df['sampling_point'].isin(sampling_points)) &
            (self.df['parameter'] == parameter) &
            (self.df['value'].notna())
        ]

        if filtered.empty:
            return 0, 0

        total_count = len(filtered)
        nc_count = filtered['value'].apply(condition).sum()

        return int(nc_count), int(total_count)

    def get_recycle_water_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get recycle water statistics from water quality data
        - Turbidity (NTU)
        - Conductivity (µS/cm)

        Returns:
            Dictionary with count for each parameter
        """
        if self.df.empty:
            return {}

        result = {}

        # Filter data for recycle water parameters
        # Only count where sampling_point is 'recycle water'
        for param_name in ['Turbidity', 'Conductivity']:
            param_data = self.df[
                (self.df['parameter'] == param_name) &
                (self.df['sampling_point'] == 'recycle water') &
                (self.df['value'].notna())
            ]

            if not param_data.empty:
                result[param_name] = {
                    'count': len(param_data)
                }

        return result

    def get_statistics_with_count(self, sampling_points, parameter, apply_filter: bool = False) -> Dict[str, any]:
        """
        Calculate statistics with total sample count

        Args:
            sampling_points: List of sampling points (or group name like 'TW', 'FW')
            parameter: Parameter name
            apply_filter: Whether to apply @RW<100 filtering

        Returns:
            Dictionary with mean, p95, p100, and total_count
        """
        # If sampling_points is a string (group name), get appropriate points for parameter
        if isinstance(sampling_points, str):
            sampling_points = self.get_sampling_points_for_parameter(parameter, sampling_points)

        df_to_use = self.apply_rw_filtering() if apply_filter else self.df

        filtered = df_to_use[
            (df_to_use['sampling_point'].isin(sampling_points)) &
            (df_to_use['parameter'] == parameter) &
            (df_to_use['value'].notna())
        ]

        if filtered.empty:
            return {'mean': np.nan, 'p95': np.nan, 'p100': np.nan, 'total_count': 0}

        return {
            'mean': filtered['value'].mean(),
            'p95': filtered['value'].quantile(0.95),
            'p100': filtered['value'].max(),
            'total_count': len(filtered)
        }

    def get_daily_counts_for_parameter_group(
        self,
        parameter: str,
        group: str,
        year: int,
        month: int
    ) -> pd.DataFrame:
        """
        Get daily measurement counts for specific parameter+group

        Args:
            parameter: Parameter name (e.g., 'Turbidity', 'pH')
            group: Group name (RW, CW, FW, TW)
            year: Year (e.g., 2025)
            month: Month (1-12)

        Returns:
            DataFrame with columns [day, count]
            - day: 1-31 (depending on month)
            - count: number of measurements on that day
        """
        if self.df.empty:
            return pd.DataFrame(columns=['day', 'count'])

        # Get appropriate sampling points for this parameter+group
        sampling_points = self.get_sampling_points_for_parameter(parameter, group)

        # Filter by year, month, parameter, and sampling points
        filtered = self.df[
            (self.df['parameter'] == parameter) &
            (self.df['sampling_point'].isin(sampling_points)) &
            (self.df['value'].notna())
        ].copy()

        if filtered.empty:
            # Return all days with 0 count
            days_in_month = pd.Period(f'{year}-{month:02d}').days_in_month
            return pd.DataFrame({
                'day': range(1, days_in_month + 1),
                'count': [0] * days_in_month
            })

        # Extract day from date column (assuming YYYY-MM-DD format)
        filtered['day'] = pd.to_datetime(filtered['date']).dt.day

        # Filter by selected year and month
        filtered = filtered[
            (pd.to_datetime(filtered['date']).dt.year == year) &
            (pd.to_datetime(filtered['date']).dt.month == month)
        ]

        # Count measurements per day
        daily_counts = filtered.groupby('day').size().reset_index(name='count')

        # Get number of days in selected month
        days_in_month = pd.Period(f'{year}-{month:02d}').days_in_month

        # Create complete day range and merge
        all_days = pd.DataFrame({'day': range(1, days_in_month + 1)})
        result = all_days.merge(daily_counts, on='day', how='left').fillna(0)
        result['count'] = result['count'].astype(int)

        return result


class JarTestProcessor:
    """Process Jar Test data"""

    def __init__(self, df: pd.DataFrame):
        """
        Initialize processor

        Args:
            df: Jar test DataFrame
        """
        self.df = df.copy()

    def count_chemical_usage_per_month(self) -> pd.Series:
        """
        Count chemical usage (once per shift)

        Logic:
        - Each shift (08.00-16.00 or 16.00-24.00) with any jar test = 1 count
        - Sum all shifts in the month

        Returns:
            Series with chemical counts
        """
        if self.df.empty:
            return pd.Series()

        # Filter only relevant shifts (exclude 00.00-08.00)
        df_shifts = self.df[
            self.df['time_period'].isin(['08.00-16.00', '16.00-24.00'])
        ].copy()

        # Remove rows where chemical is NaN or dose is NaN (no actual test data)
        df_shifts = df_shifts[
            (df_shifts['chemical'].notna()) &
            (df_shifts['dose'].notna())
        ].copy()

        if df_shifts.empty:
            return pd.Series()

        # Count unique date + time_period + chemical combinations
        # Each shift with any jar test for a chemical = 1 count
        # First, get unique combinations of date + time_period + chemical
        unique_combinations = df_shifts[['date', 'time_period', 'chemical']].drop_duplicates()
        # Then count occurrences per chemical
        chemical_counts = unique_combinations.groupby(['chemical']).size()

        return chemical_counts

    def count_recycle_water_parameters(self) -> Dict[str, pd.DataFrame]:
        """
        Count recycle water (น้ำนำกลับ) parameters
        - Turbidity
        - Conductivity

        Returns:
            Dictionary with statistics for each parameter
        """
        if self.df.empty:
            return {}

        result = {}

        for param in ['turbidity', 'conductivity']:
            param_data = self.df[self.df['chemical'].str.contains(param, case=False, na=False)]

            if not param_data.empty:
                result[param] = {
                    'count': len(param_data),
                    'mean': param_data['dose'].mean() if 'dose' in param_data.columns else np.nan
                }

        return result
