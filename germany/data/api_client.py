"""
Energy-Charts API client for German power market data.
Data source: Fraunhofer ISE (https://api.energy-charts.info/)
"""

import time
from datetime import datetime, timedelta

import pandas as pd
import requests

BASE_URL = "https://api.energy-charts.info"
TIMEOUT = 30

# Simple in-memory cache: {cache_key: (timestamp, data)}
_cache: dict[str, tuple[float, pd.DataFrame]] = {}
CACHE_TTL = 300  # 5 minutes


def _cache_key(endpoint: str, params: dict) -> str:
    sorted_params = sorted(params.items())
    return f"{endpoint}|{'|'.join(f'{k}={v}' for k, v in sorted_params)}"


def _get_cached(key: str) -> pd.DataFrame | None:
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return data
        del _cache[key]
    return None


def _set_cache(key: str, data: pd.DataFrame) -> None:
    _cache[key] = (time.time(), data)


def _format_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def _api_get(endpoint: str, params: dict) -> dict:
    url = f"{BASE_URL}{endpoint}"
    resp = requests.get(url, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def fetch_day_ahead_prices(
    start: datetime | None = None,
    end: datetime | None = None,
) -> pd.DataFrame:
    """Fetch hourly day-ahead prices for Germany (EUR/MWh)."""
    if end is None:
        end = datetime.now()
    if start is None:
        start = end - timedelta(days=7)

    params = {
        "bzn": "DE-LU",
        "start": _format_date(start),
        "end": _format_date(end),
    }
    key = _cache_key("/price", params)
    cached = _get_cached(key)
    if cached is not None:
        return cached

    data = _api_get("/price", params)

    unix_seconds = data.get("unix_seconds", [])
    price = data.get("price", [])

    if not unix_seconds or not price:
        return pd.DataFrame(columns=["timestamp", "price_eur_mwh"])

    df = pd.DataFrame({
        "timestamp": pd.to_datetime(unix_seconds, unit="s", utc=True),
        "price_eur_mwh": price,
    })
    df["timestamp"] = df["timestamp"].dt.tz_convert(
        "Europe/Berlin"
    )
    df = df.sort_values("timestamp").reset_index(drop=True)
    _set_cache(key, df)
    return df


def fetch_generation_by_source(
    start: datetime | None = None,
    end: datetime | None = None,
) -> pd.DataFrame:
    """Fetch 15-min generation data by source for Germany."""
    if end is None:
        end = datetime.now()
    if start is None:
        start = end - timedelta(days=7)

    params = {
        "country": "de",
        "start": _format_date(start),
        "end": _format_date(end),
    }
    key = _cache_key("/public_power", params)
    cached = _get_cached(key)
    if cached is not None:
        return cached

    data = _api_get("/public_power", params)

    unix_seconds = data.get("unix_seconds", [])
    if not unix_seconds:
        return pd.DataFrame(columns=["timestamp"])

    records: dict[str, list] = {
        "timestamp": pd.to_datetime(
            unix_seconds, unit="s", utc=True
        ),
    }

    # Map API production type names to clean column names
    source_map = {
        "Solar": "solar",
        "Wind onshore": "wind_onshore",
        "Wind offshore": "wind_offshore",
        "Fossil gas": "gas",
        "Fossil coal-derived gas": "gas",
        "Fossil hard coal": "hard_coal",
        "Fossil brown coal / lignite": "lignite",
        "Hydro Run-of-River": "hydro",
        "Hydro water reservoir": "hydro",
        "Biomass": "biomass",
        "Nuclear": "nuclear",
        "Fossil oil": "oil",
        "Hydro pumped storage": "pumped_storage",
        "Geothermal": "geothermal",
        "Others": "other",
        "Waste": "other",
    }

    prod_types = data.get("production_types", [])
    for entry in prod_types:
        name = entry.get("name", "")
        values = entry.get("data", [])
        col_name = source_map.get(name)
        if col_name and values:
            cleaned = [
                v if v is not None else 0
                for v in values
            ]
            if col_name in records:
                # Sum when multiple API types map
                # to the same column
                records[col_name] = [
                    a + b
                    for a, b in zip(
                        records[col_name], cleaned
                    )
                ]
            else:
                records[col_name] = cleaned

    df = pd.DataFrame(records)
    df["timestamp"] = df["timestamp"].dt.tz_convert(
        "Europe/Berlin"
    )
    df = df.sort_values("timestamp").reset_index(drop=True)
    _set_cache(key, df)
    return df


def fetch_total_load(
    start: datetime | None = None,
    end: datetime | None = None,
) -> pd.DataFrame:
    """Fetch total electricity load for Germany."""
    if end is None:
        end = datetime.now()
    if start is None:
        start = end - timedelta(days=7)

    params = {
        "country": "de",
        "start": _format_date(start),
        "end": _format_date(end),
    }
    key = _cache_key("/total_power", params)
    cached = _get_cached(key)
    if cached is not None:
        return cached

    data = _api_get("/total_power", params)

    unix_seconds = data.get("unix_seconds", [])

    load_data = None
    for entry in data.get("production_types", []):
        name = entry.get("name", "")
        if "load" in name.lower() and "residual" not in name.lower() and "renewable" not in name.lower():
            load_data = entry.get("data", [])
            break

    if not unix_seconds or load_data is None:
        return pd.DataFrame(
            columns=["timestamp", "load_mw"]
        )

    df = pd.DataFrame({
        "timestamp": pd.to_datetime(
            unix_seconds, unit="s", utc=True
        ),
        "load_mw": load_data,
    })
    df = df.dropna(subset=["load_mw"])
    df["timestamp"] = df["timestamp"].dt.tz_convert(
        "Europe/Berlin"
    )
    df = df.sort_values("timestamp").reset_index(drop=True)
    _set_cache(key, df)
    return df


def fetch_installed_capacity() -> pd.DataFrame:
    """Fetch current installed capacity by source (MW)."""
    key = _cache_key("/installed_power", {"country": "de"})
    cached = _get_cached(key)
    if cached is not None:
        return cached

    data = _api_get(
        "/installed_power",
        {"country": "de", "time_step": "yearly"},
    )

    rows = []
    for entry in data.get("production_types", []):
        name = entry.get("name", "")
        values = entry.get("data", [])
        if values:
            # Take the latest non-None value
            latest = None
            for v in reversed(values):
                if v is not None:
                    latest = v
                    break
            if latest is not None:
                rows.append({
                    "source": name,
                    "capacity_mw": latest,
                })

    df = pd.DataFrame(rows)
    _set_cache(key, df)
    return df


def fetch_cross_border_flows(
    start: datetime | None = None,
    end: datetime | None = None,
) -> pd.DataFrame:
    """Fetch cross-border electricity flows for Germany."""
    if end is None:
        end = datetime.now()
    if start is None:
        start = end - timedelta(days=7)

    params = {
        "country": "de",
        "start": _format_date(start),
        "end": _format_date(end),
    }
    key = _cache_key("/cbpf", params)
    cached = _get_cached(key)
    if cached is not None:
        return cached

    try:
        data = _api_get("/cbpf", params)
    except requests.HTTPError:
        return pd.DataFrame(
            columns=["timestamp", "country", "flow_mw"]
        )

    unix_seconds = data.get("unix_seconds", [])
    if not unix_seconds:
        return pd.DataFrame(
            columns=["timestamp", "country", "flow_mw"]
        )

    timestamps = pd.to_datetime(
        unix_seconds, unit="s", utc=True
    ).tz_convert("Europe/Berlin")

    rows = []
    for entry in data.get("production_types", []):
        name = entry.get("name", "")
        values = entry.get("data", [])
        if values:
            for ts, v in zip(timestamps, values):
                if v is not None:
                    rows.append({
                        "timestamp": ts,
                        "country": name,
                        "flow_mw": v,
                    })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("timestamp").reset_index(
            drop=True
        )
    _set_cache(key, df)
    return df


def clear_cache() -> None:
    """Clear the in-memory API cache."""
    _cache.clear()
