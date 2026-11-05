"""Inclusive export dates; all run dates use Asia/Shanghai."""
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

CALENDAR = Path(__file__).resolve().parents[1] / 'config/holidays.json'

def shanghai_today():
    return datetime.now(ZoneInfo('Asia/Shanghai')).date()

def load_calendar(path=CALENDAR):
    p = Path(path)
    config = json.loads(p.read_text()) if p.exists() else {}
    holidays, workdays = set(config.get('holidays', {})), set(config.get('workdays', {}))
    if holidays & workdays: raise ValueError('calendar-conflict: a date is holiday and workday')
    for value in holidays | workdays: date.fromisoformat(value)
    return config, holidays, workdays

def is_workday(day, holidays, workdays):
    return day.isoformat() in workdays or (day.isoformat() not in holidays and day.weekday() < 5)

def compute(today=None, start=None, end=None, force=False, calendar_path=CALENDAR):
    today = date.fromisoformat(today) if isinstance(today, str) else today or shanghai_today()
    if bool(start) != bool(end): raise ValueError('range-invalid: --start and --end must be provided together')
    if start:
        first, last = date.fromisoformat(start), date.fromisoformat(end)
        if first > last: raise ValueError('range-invalid: start is after end')
        return {'ok': True, 'today': today.isoformat(), 'start': first.isoformat(), 'end': last.isoformat(),
                'end_exclusive': (last + timedelta(days=1)).isoformat(), 'days': (last-first).days+1,
                'mode': 'manual', 'warnings': []}
    cfg, holidays, extra = load_calendar(calendar_path)
    covered = set(cfg.get('covered_years', [])); warnings = []
    if today.year not in covered: warnings.append('calendar-year-unverified: weekend-only fallback; review dates')
    if not is_workday(today, holidays, extra) and not force:
        return {'ok': False, 'today': today.isoformat(), 'reason': 'today_not_workday', 'warnings': warnings}
    first = today - timedelta(days=1)
    for _ in range(370):
        if is_workday(first, holidays, extra): break
        first -= timedelta(days=1)
    else: raise ValueError('calendar-invalid: cannot find previous workday')
    if first.year not in covered and first.year != today.year: warnings.append('calendar-cross-year-unverified')
    last = today - timedelta(days=1)
    return {'ok': True, 'today': today.isoformat(), 'start': first.isoformat(), 'end': last.isoformat(),
            'end_exclusive': today.isoformat(), 'days': (today-first).days,
            'mode': 'forced' if force else 'auto', 'warnings': warnings}
