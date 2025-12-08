"""Dashboard trend rollup utilities."""
import json
import logging
from bisect import bisect_right
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Sequence, Tuple

from database import get_db_connection
from app.constants.database import (
    TABLE_VULNERABILITY_SNAPSHOTS,
    TABLE_VULNERABILITY_TREND_PERIODS,
)
from app.utils.cache import cache_get, cache_set

logger = logging.getLogger(__name__)

PeriodType = str
SUPPORTED_PERIODS: Tuple[PeriodType, ...] = ("week", "month", "year")
TREND_CACHE_PREFIX = "dashboard:trend-periods"
TREND_CACHE_TTL = 300


@dataclass
class DailySnapshot:
    date_value: date
    snapshot_id: int
    critical: int
    high: int
    medium: int


def refresh_trend_periods(period_types: Optional[Sequence[PeriodType]] = None, reference_date: Optional[date] = None) -> int:
    """Materialize trend data for the requested periods.

    Args:
        period_types: Sequence of period identifiers to refresh.
        reference_date: Anchor date for determining natural week/month/year.

    Returns:
        int: Number of periods refreshed.
    """
    _validate_periods(period_types)
    target_periods = _normalize_periods(period_types)

    anchor_date = reference_date or datetime.utcnow().date()
    connection = get_db_connection()
    if not connection:
        raise Exception("数据库连接失败")

    try:
        cursor = connection.cursor(dictionary=True)
        daily_series = _load_daily_series(cursor)
        if not daily_series:
            logger.warning("No snapshot data available; skipping trend rollup")
            return 0

        ordered_dates = [item.date_value for item in daily_series]
        date_map = {item.date_value: item for item in daily_series}

        updated = 0
        for period_type in target_periods:
            bounds = _calculate_period_bounds(period_type, anchor_date)
            points, last_counts, source_ids, carry_flag = _build_period_points(
                period_type,
                bounds,
                daily_series,
                ordered_dates,
                date_map,
            )
            if not points:
                logger.warning("Skipping period %s: no points computed", period_type)
                continue
            _upsert_period_row(
                cursor,
                period_type,
                bounds,
                points,
                last_counts,
                source_ids,
                carry_flag,
            )
            updated += 1

        connection.commit()
        return updated
    finally:
        if connection and connection.is_connected():
            connection.close()


def fetch_trend_payload(
    period_types: Optional[Sequence[PeriodType]] = None,
    use_cache: bool = True,
    auto_refresh: bool = True,
) -> Dict[PeriodType, List[Dict[str, int]]]:
    """High-level helper that applies caching and optional refresh."""
    _validate_periods(period_types)
    target_periods = _normalize_periods(period_types)
    cache_key = _build_cache_key(target_periods)
    if use_cache:
        cached = cache_get(cache_key)
        if cached:
            return cached

    trends = get_trend_periods(target_periods)
    normalized = _ensure_all_periods(trends, target_periods)

    if auto_refresh and any(len(normalized[period]) == 0 for period in target_periods):
        refreshed = refresh_trend_periods(target_periods)
        if refreshed:
            trends = get_trend_periods(target_periods)
            normalized = _ensure_all_periods(trends, target_periods)

    if use_cache:
        cache_set(cache_key, normalized, ttl=TREND_CACHE_TTL)
    return normalized


def get_trend_periods(period_types: Optional[Sequence[PeriodType]] = None) -> Dict[PeriodType, List[Dict[str, int]]]:
    """Load materialized trend data from the DB.

    Args:
        period_types: Optional subset of periods to fetch.

    Returns:
        dict: period_type -> list of point dicts.
    """
    _validate_periods(period_types)
    target_periods = _normalize_periods(period_types)

    connection = get_db_connection()
    if not connection:
        raise Exception("数据库连接失败")

    try:
        cursor = connection.cursor(dictionary=True)
        placeholders = ",".join(["%s"] * len(target_periods))
        query = f"""
        SELECT period_type, data_points
        FROM {TABLE_VULNERABILITY_TREND_PERIODS}
        WHERE period_type IN ({placeholders})
        ORDER BY period_type ASC
        """
        params = list(target_periods)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        result: Dict[PeriodType, List[Dict[str, int]]] = {}
        for row in rows:
            try:
                points = json.loads(row['data_points'])
            except (TypeError, json.JSONDecodeError):
                points = []
            result[row['period_type']] = points
        return result
    finally:
        cursor.close()
        connection.close()


def _load_daily_series(cursor) -> List[DailySnapshot]:
    """Construct distinct daily snapshot records keeping the latest entry per day."""
    cursor.execute(
        f"""
        SELECT id, snapshot_time, critical_count, high_count, medium_count
        FROM {TABLE_VULNERABILITY_SNAPSHOTS}
        ORDER BY snapshot_time ASC
        """
    )
    rows = cursor.fetchall()
    latest_per_day: Dict[date, Dict[str, int]] = {}
    for row in rows:
        snapshot_time = row['snapshot_time']
        if not snapshot_time:
            continue
        if isinstance(snapshot_time, str):
            snapshot_time = datetime.fromisoformat(snapshot_time)
        day_key = snapshot_time.date()
        existing = latest_per_day.get(day_key)
        if not existing or snapshot_time > existing['snapshot_time']:
            latest_per_day[day_key] = {
                'snapshot_time': snapshot_time,
                'id': row['id'],
                'critical': row.get('critical_count') or 0,
                'high': row.get('high_count') or 0,
                'medium': row.get('medium_count') or 0,
            }

    daily_series = [
        DailySnapshot(
            date_value=day,
            snapshot_id=data['id'],
            critical=data['critical'],
            high=data['high'],
            medium=data['medium'],
        )
        for day, data in sorted(latest_per_day.items(), key=lambda item: item[0])
    ]
    return daily_series


@dataclass
class PeriodBounds:
    period_type: PeriodType
    start: date
    end: date
    label: str


def _calculate_period_bounds(period_type: PeriodType, anchor_date: date) -> PeriodBounds:
    """Compute natural period bounds anchored to the given date."""
    if period_type == 'week':
        start = anchor_date - timedelta(days=anchor_date.weekday())
        end = start + timedelta(days=6)
        iso_year, iso_week, _ = start.isocalendar()
        label = f"{iso_year}-W{iso_week:02d}"
    elif period_type == 'month':
        start = anchor_date.replace(day=1)
        days_in_month = monthrange(start.year, start.month)[1]
        end = start.replace(day=days_in_month)
        label = start.strftime("%Y-%m")
    elif period_type == 'year':
        start_of_year = date(anchor_date.year, 1, 1)
        start = start_of_year
        end = date(anchor_date.year, 12, 31)
        label = start_of_year.strftime("%Y")
    else:
        raise ValueError(f"Unsupported period type: {period_type}")
    return PeriodBounds(period_type=period_type, start=start, end=end, label=label)


def _build_period_points(
    period_type: PeriodType,
    bounds: PeriodBounds,
    daily_series: List[DailySnapshot],
    ordered_dates: List[date],
    date_map: Dict[date, DailySnapshot],
) -> Tuple[List[Dict[str, int]], Dict[str, int], List[int], bool]:
    """Construct data points for the required date range."""
    if bounds.start > bounds.end:
        return [], {'critical': 0, 'high': 0, 'medium': 0}, [], False

    points: List[Dict[str, int]] = []
    carry_used = False
    source_ids = set()
    last_counts = {'critical': 0, 'high': 0, 'medium': 0}

    for offset in range((bounds.end - bounds.start).days + 1):
        current_day = bounds.start + timedelta(days=offset)
        snapshot = date_map.get(current_day)
        is_carry = False
        if snapshot:
            counts = {
                'critical': snapshot.critical,
                'high': snapshot.high,
                'medium': snapshot.medium,
            }
            snapshot_id = snapshot.snapshot_id
        else:
            snapshot = _find_previous_snapshot(daily_series, ordered_dates, current_day)
            if snapshot:
                counts = {
                    'critical': snapshot.critical,
                    'high': snapshot.high,
                    'medium': snapshot.medium,
                }
                snapshot_id = snapshot.snapshot_id
            else:
                counts = {'critical': 0, 'high': 0, 'medium': 0}
                snapshot_id = None
            is_carry = True
        if is_carry:
            carry_used = True
        if snapshot_id:
            source_ids.add(snapshot_id)
        points.append({
            'date': current_day.isoformat(),
            'critical': counts['critical'],
            'high': counts['high'],
            'medium': counts['medium'],
            'carry': is_carry,
        })
        last_counts = counts

    return points, last_counts, sorted(source_ids), carry_used


def _find_previous_snapshot(
    daily_series: List[DailySnapshot],
    ordered_dates: List[date],
    target_day: date,
) -> Optional[DailySnapshot]:
    """Find the most recent snapshot on or before the target day."""
    if not ordered_dates:
        return None
    idx = bisect_right(ordered_dates, target_day)
    if idx == 0:
        return None
    return daily_series[idx - 1]


def _upsert_period_row(
    cursor,
    period_type: PeriodType,
    bounds: PeriodBounds,
    points: List[Dict[str, int]],
    last_counts: Dict[str, int],
    source_ids: List[int],
    carry_flag: bool,
) -> None:
    """Persist computed period data into the materialized table."""
    query = f"""
    INSERT INTO {TABLE_VULNERABILITY_TREND_PERIODS} (
        period_type,
        period_label,
        period_start,
        period_end,
        critical_active,
        high_active,
        medium_active,
        data_points,
        source_snapshot_ids,
        is_carry_forward
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        period_label = VALUES(period_label),
        period_end = VALUES(period_end),
        critical_active = VALUES(critical_active),
        high_active = VALUES(high_active),
        medium_active = VALUES(medium_active),
        data_points = VALUES(data_points),
        source_snapshot_ids = VALUES(source_snapshot_ids),
        is_carry_forward = VALUES(is_carry_forward),
        updated_at = CURRENT_TIMESTAMP
    """
    cursor.execute(
        query,
        (
            period_type,
            bounds.label,
            bounds.start,
            bounds.end,
            last_counts['critical'],
            last_counts['high'],
            last_counts['medium'],
            json.dumps(points),
            json.dumps(source_ids),
            carry_flag,
        ),
    )


def _ensure_all_periods(
    data: Dict[PeriodType, List[Dict[str, int]]],
    target_periods: Sequence[PeriodType],
) -> Dict[PeriodType, List[Dict[str, int]]]:
    """Guarantee presence of every requested period key."""
    normalized: Dict[PeriodType, List[Dict[str, int]]] = {}
    for period in target_periods:
        normalized[period] = data.get(period, [])
    return normalized


def _build_cache_key(period_types: Sequence[PeriodType]) -> str:
    if not period_types:
        return f"{TREND_CACHE_PREFIX}:all"
    ordered = _normalize_periods(period_types)
    suffix = "-".join(ordered)
    return f"{TREND_CACHE_PREFIX}:{suffix}"


def _normalize_periods(period_types: Optional[Sequence[PeriodType]]) -> Tuple[PeriodType, ...]:
    if not period_types:
        return SUPPORTED_PERIODS
    ordered: List[PeriodType] = []
    for candidate in SUPPORTED_PERIODS:
        if candidate in period_types:
            ordered.append(candidate)
    return tuple(ordered)


def _validate_periods(period_types: Optional[Sequence[PeriodType]]) -> None:
    if not period_types:
        return
    invalid = [period for period in period_types if period not in SUPPORTED_PERIODS]
    if invalid:
        raise ValueError(f"Unsupported period types requested: {invalid}")
