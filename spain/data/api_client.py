"""
REE API client for Spanish power market data.
Data source: Red Electrica de Espana (https://apidatos.ree.es/)
Public API — no authentication required.

API constraints discovered:
- Prices support time_trunc=hour
- Generation, demand, flows support time_trunc=day (NOT hour)
- Interconnection flows use /francia-frontera (not -fisicos)
"""

import time
from datetime import datetime, timedelta

import pandas as pd
import requests

BASE_URL = "https://apidatos.ree.es"
TIMEOUT = 30

# Simple in-memory cache: {cache_key: (timestamp, data)}
_cache: dict[str, tuple[float, object]] = {}
CACHE_TTL = 900  # 15 minutes — strategic data is less time-sensitive


def _cache_key(endpoint: str, params: dict) -> str:
    sorted_params = sorted(params.items())
    return (
        f"{endpoint}|"
        f"{'|'.join(f'{k}={v}' for k, v in sorted_params)}"
    )


def _get_cached(key: str) -> object | None:
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return data
        del _cache[key]
    return None


def _set_cache(key: str, data: object) -> None:
    _cache[key] = (time.time(), data)


def _format_dt(dt: datetime) -> str:
    """Format datetime for REE API (ISO 8601)."""
    return dt.strftime("%Y-%m-%dT%H:%M")


def _api_get(endpoint: str, params: dict) -> dict:
    """Make a GET request to the REE API."""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    resp = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def _parse_included(
    data: dict,
) -> list[dict]:
    """Extract the included[] array from REE response."""
    return data.get("included", [])


def fetch_day_ahead_prices(
    start: datetime | None = None,
    end: datetime | None = None,
) -> pd.DataFrame:
    """Fetch hourly day-ahead spot prices for Spain (EUR/MWh)."""
    if end is None:
        end = datetime.now()
    if start is None:
        start = end - timedelta(days=7)

    params = {
        "start_date": _format_dt(start),
        "end_date": _format_dt(end),
        "time_trunc": "hour",
    }
    endpoint = (
        "/en/datos/mercados"
        "/precios-mercados-tiempo-real"
    )
    key = _cache_key(endpoint, params)
    cached = _get_cached(key)
    if cached is not None:
        return cached

    try:
        data = _api_get(endpoint, params)
    except requests.HTTPError:
        return pd.DataFrame(
            columns=["timestamp", "price_eur_mwh"]
        )

    rows = []
    for item in _parse_included(data):
        values = (
            item.get("attributes", {})
            .get("values", [])
        )
        for v in values:
            if v.get("value") is not None:
                rows.append({
                    "timestamp": v["datetime"],
                    "price_eur_mwh": v["value"],
                })
        if rows:
            break  # Use first series

    if not rows:
        return pd.DataFrame(
            columns=["timestamp", "price_eur_mwh"]
        )

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(
        df["timestamp"], utc=True
    )
    df["timestamp"] = df["timestamp"].dt.tz_convert(
        "Europe/Madrid"
    )
    df = df.sort_values("timestamp").reset_index(
        drop=True
    )
    _set_cache(key, df)
    return df


def fetch_generation_by_source(
    start: datetime | None = None,
    end: datetime | None = None,
    time_trunc: str = "day",
) -> pd.DataFrame:
    """Fetch generation data by source for Spain.

    Args:
        start: Start datetime.
        end: End datetime.
        time_trunc: Time resolution — "day" or "month".
    """
    if end is None:
        end = datetime.now()
    if start is None:
        start = end - timedelta(days=7)

    params = {
        "start_date": _format_dt(start),
        "end_date": _format_dt(end),
        "time_trunc": time_trunc,
    }
    endpoint = (
        "/en/datos/generacion"
        "/estructura-generacion"
    )
    key = _cache_key(endpoint, params)
    cached = _get_cached(key)
    if cached is not None:
        return cached

    try:
        data = _api_get(endpoint, params)
    except requests.HTTPError:
        return pd.DataFrame(columns=["timestamp"])

    # Map actual REE API source names
    source_map = {
        "hydro": "hydro",
        "nuclear": "nuclear",
        "coal": "coal",
        "diesel engines": "oil",
        "gas turbine": "gas",
        "steam turbine": "gas",
        "combined cycle": "combined_cycle",
        "hydroeolian": "other",
        "wind": "wind",
        "solar photovoltaic": "solar_pv",
        "thermal solar": "solar_thermal",
        "other renewables": "other",
        "cogeneration": "cogeneration",
        "non-renewable waste": "waste",
        "renewable waste": "biomass",
    }

    items = _parse_included(data)
    if not items:
        return pd.DataFrame(columns=["timestamp"])

    # Build records by timestamp
    ts_set = set()
    series_data: dict[str, dict[str, float]] = {}

    for item in items:
        raw_name = (
            item.get("attributes", {})
            .get("title", item.get("type", ""))
            .lower()
            .strip()
        )
        # Skip the total row
        if "total" in raw_name:
            continue
        col_name = source_map.get(raw_name)
        if col_name is None:
            # Try partial matching
            for pattern, mapped in source_map.items():
                if pattern in raw_name:
                    col_name = mapped
                    break
        if col_name is None:
            continue

        values = (
            item.get("attributes", {})
            .get("values", [])
        )
        for v in values:
            dt_str = v.get("datetime")
            val = v.get("value")
            if dt_str is None or val is None:
                continue
            ts_set.add(dt_str)
            if dt_str not in series_data:
                series_data[dt_str] = {}
            if col_name in series_data[dt_str]:
                series_data[dt_str][col_name] += val
            else:
                series_data[dt_str][col_name] = val

    if not series_data:
        return pd.DataFrame(columns=["timestamp"])

    rows = []
    for ts_str in sorted(ts_set):
        row = {"timestamp": ts_str}
        row.update(series_data[ts_str])
        rows.append(row)

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(
        df["timestamp"], utc=True
    )
    df["timestamp"] = df["timestamp"].dt.tz_convert(
        "Europe/Madrid"
    )
    df = df.fillna(0)
    df = df.sort_values("timestamp").reset_index(
        drop=True
    )
    _set_cache(key, df)
    return df


def fetch_total_load(
    start: datetime | None = None,
    end: datetime | None = None,
    time_trunc: str = "day",
) -> pd.DataFrame:
    """Fetch total electricity demand for Spain.

    Args:
        start: Start datetime.
        end: End datetime.
        time_trunc: Time resolution — "day" or "month".
    """
    if end is None:
        end = datetime.now()
    if start is None:
        start = end - timedelta(days=7)

    params = {
        "start_date": _format_dt(start),
        "end_date": _format_dt(end),
        "time_trunc": time_trunc,
    }
    endpoint = "/en/datos/demanda/evolucion"
    key = _cache_key(endpoint, params)
    cached = _get_cached(key)
    if cached is not None:
        return cached

    try:
        data = _api_get(endpoint, params)
    except requests.HTTPError:
        return pd.DataFrame(
            columns=["timestamp", "load_mw"]
        )

    rows = []
    for item in _parse_included(data):
        values = (
            item.get("attributes", {})
            .get("values", [])
        )
        for v in values:
            if v.get("value") is not None:
                rows.append({
                    "timestamp": v["datetime"],
                    "load_mw": v["value"],
                })
        if rows:
            break  # Use first series (Demand)

    if not rows:
        return pd.DataFrame(
            columns=["timestamp", "load_mw"]
        )

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(
        df["timestamp"], utc=True
    )
    df["timestamp"] = df["timestamp"].dt.tz_convert(
        "Europe/Madrid"
    )
    df = df.dropna(subset=["load_mw"])
    df = df.sort_values("timestamp").reset_index(
        drop=True
    )
    _set_cache(key, df)
    return df


def fetch_cross_border_flows(
    start: datetime | None = None,
    end: datetime | None = None,
    country: str = "all",
    time_trunc: str = "day",
) -> pd.DataFrame:
    """Fetch cross-border electricity flows for Spain.

    Uses the /frontera endpoints (not -fisicos).
    Extracts the 'saldo' (balance) series.

    Args:
        start: Start datetime.
        end: End datetime.
        country: 'france', 'portugal', 'morocco', or
            'all' for all borders.
        time_trunc: Time resolution — "day" or "month".
    """
    if end is None:
        end = datetime.now()
    if start is None:
        start = end - timedelta(days=7)

    border_endpoints = {
        "france": (
            "/en/datos/intercambios"
            "/francia-frontera"
        ),
        "portugal": (
            "/en/datos/intercambios"
            "/portugal-frontera"
        ),
        "morocco": (
            "/en/datos/intercambios"
            "/marruecos-frontera"
        ),
    }

    if country != "all":
        endpoints = {
            country: border_endpoints.get(
                country, ""
            )
        }
    else:
        endpoints = border_endpoints

    params = {
        "start_date": _format_dt(start),
        "end_date": _format_dt(end),
        "time_trunc": time_trunc,
    }

    all_rows = []
    for border_name, endpoint in endpoints.items():
        if not endpoint:
            continue
        key = _cache_key(endpoint, params)
        cached = _get_cached(key)
        if cached is not None:
            all_rows.extend(cached)
            continue

        try:
            data = _api_get(endpoint, params)
        except requests.HTTPError:
            continue

        border_rows = []
        # Look for the "saldo" (balance) series
        for item in _parse_included(data):
            title = (
                item.get("attributes", {})
                .get(
                    "title", item.get("type", "")
                )
                .lower()
            )
            if "saldo" not in title:
                continue
            values = (
                item.get("attributes", {})
                .get("values", [])
            )
            for v in values:
                if v.get("value") is not None:
                    border_rows.append({
                        "timestamp": v["datetime"],
                        "country": border_name.title(),
                        "flow_mw": v["value"],
                    })
            break

        _set_cache(key, border_rows)
        all_rows.extend(border_rows)

    if not all_rows:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "country",
                "flow_mw",
            ]
        )

    df = pd.DataFrame(all_rows)
    df["timestamp"] = pd.to_datetime(
        df["timestamp"], utc=True
    )
    df["timestamp"] = df["timestamp"].dt.tz_convert(
        "Europe/Madrid"
    )
    df = df.sort_values("timestamp").reset_index(
        drop=True
    )
    return df


def fetch_renewable_vs_nonrenewable(
    start: datetime | None = None,
    end: datetime | None = None,
    time_trunc: str = "day",
) -> pd.DataFrame:
    """Fetch renewable vs non-renewable generation.

    Args:
        start: Start datetime.
        end: End datetime.
        time_trunc: Time resolution — "day" or "month".
    """
    if end is None:
        end = datetime.now()
    if start is None:
        start = end - timedelta(days=7)

    params = {
        "start_date": _format_dt(start),
        "end_date": _format_dt(end),
        "time_trunc": time_trunc,
    }
    endpoint = (
        "/en/datos/generacion"
        "/evolucion-renovable-no-renovable"
    )
    key = _cache_key(endpoint, params)
    cached = _get_cached(key)
    if cached is not None:
        return cached

    try:
        data = _api_get(endpoint, params)
    except requests.HTTPError:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "renewable_mw",
                "non_renewable_mw",
            ]
        )

    series: dict[str, list] = {}
    for item in _parse_included(data):
        raw_name = (
            item.get("attributes", {})
            .get("title", item.get("type", ""))
            .lower()
        )
        if (
            "renew" in raw_name
            or "renovable" in raw_name
        ):
            if (
                "non" in raw_name
                or "no " in raw_name
            ):
                col = "non_renewable_mw"
            else:
                col = "renewable_mw"
        else:
            continue
        values = (
            item.get("attributes", {})
            .get("values", [])
        )
        for v in values:
            if v.get("value") is not None:
                if col not in series:
                    series[col] = []
                series[col].append({
                    "timestamp": v["datetime"],
                    col: v["value"],
                })

    if not series:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "renewable_mw",
                "non_renewable_mw",
            ]
        )

    dfs = []
    for col, col_rows in series.items():
        tmp = pd.DataFrame(col_rows)
        tmp["timestamp"] = pd.to_datetime(
            tmp["timestamp"], utc=True
        )
        tmp = tmp.set_index("timestamp")
        dfs.append(tmp)

    if dfs:
        df = dfs[0].join(dfs[1:], how="outer")
    else:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "renewable_mw",
                "non_renewable_mw",
            ]
        )

    df = df.reset_index()
    df["timestamp"] = df["timestamp"].dt.tz_convert(
        "Europe/Madrid"
    )
    df = df.fillna(0)
    df = df.sort_values("timestamp").reset_index(
        drop=True
    )
    _set_cache(key, df)
    return df


def clear_cache() -> None:
    """Clear the in-memory API cache."""
    _cache.clear()
