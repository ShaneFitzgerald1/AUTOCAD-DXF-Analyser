import os
import sys
import json

def _get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), '_internal')
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TOLERANCE_PATH = os.path.join(_get_app_dir(), 'tolerances.json')

DEFAULT_TOLERANCES = {
    'block_tolerance': 1,
    'line_tolerance_1': 1,
    'line_tolerance_2': 35
}

DEFAULT_BOUNDARIES = {
    'x_min': 10,
    'x_max': 300000,
    'y_min': 10,
    'y_max': 300000
}


def _read_tolerances() -> dict:
    """Returns the full tolerances dict from the json file, or default structure if missing/corrupt."""
    if os.path.exists(TOLERANCE_PATH):
        try:
            with open(TOLERANCE_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        'active_set': 'Default',
        'sets': {'Default': DEFAULT_TOLERANCES},
        'active_boundary_set': 'Default',
        'boundary_sets': {'Default': DEFAULT_BOUNDARIES}
    }


def _write_tolerances(data: dict) -> None:
    """Writes the full tolerances dict to file."""
    os.makedirs(os.path.dirname(TOLERANCE_PATH), exist_ok=True)
    with open(TOLERANCE_PATH, 'w') as f:
        json.dump(data, f, indent=4)


# ── Tolerance sets ────────────────────────────────────────────────────────────

def get_active_tolerances() -> dict:
    """Returns the 3 tolerance values for the currently active set."""
    data = _read_tolerances()
    active = data.get('active_set', 'Default')
    return data['sets'].get(active, DEFAULT_TOLERANCES)


def get_all_tolerance_sets() -> list:
    """Returns a list of all named tolerance set names."""
    return list(_read_tolerances().get('sets', {}).keys())


def get_active_set_name() -> str:
    """Returns the name of the currently active tolerance set."""
    return _read_tolerances().get('active_set', 'Default')


def save_tolerance_set(name: str, block_tol: float, line_tol1: float, line_tol2: float) -> None:
    """Creates or updates a named tolerance set."""
    data = _read_tolerances()
    data['sets'][name] = {
        'block_tolerance': block_tol,
        'line_tolerance_1': line_tol1,
        'line_tolerance_2': line_tol2
    }
    _write_tolerances(data)


def set_active_tolerance_set(name: str) -> None:
    """Sets the active tolerance set by name."""
    data = _read_tolerances()
    if name in data['sets']:
        data['active_set'] = name
        _write_tolerances(data)


def get_all_tolerance_sets_full() -> list:
    """Returns all tolerance sets as a 2D list: [name, block_tol, line_tol1, line_tol2]"""
    sets = _read_tolerances().get('sets', {})
    return [
        [name, values['block_tolerance'], values['line_tolerance_1'], values['line_tolerance_2']]
        for name, values in sets.items()
    ]


def delete_tolerance_set(name: str) -> bool:
    """Deletes a named tolerance set. Returns True if deleted, False if not found or is Default."""
    if name == 'Default':
        return False
    data = _read_tolerances()
    if name not in data['sets']:
        return False
    del data['sets'][name]
    if data.get('active_set') == name:
        data['active_set'] = 'Default'
    _write_tolerances(data)
    return True


def extract_values_from_tolerance_sets():
    active_tolerances = get_active_tolerances()
    block_tolerance = float(active_tolerances.get('block_tolerance'))
    line_tolerance1 = float(active_tolerances.get('line_tolerance_1'))
    line_tolerance2 = float(active_tolerances.get('line_tolerance_2'))
    return block_tolerance, line_tolerance1, line_tolerance2


# ── Boundary sets ─────────────────────────────────────────────────────────────

def _get_boundary_sets(data: dict) -> dict:
    """Returns the boundary_sets dict, falling back to Default if missing."""
    return data.get('boundary_sets', {'Default': DEFAULT_BOUNDARIES})


def get_active_boundary_set_name() -> str:
    """Returns the name of the currently active boundary set."""
    return _read_tolerances().get('active_boundary_set', 'Default')


def get_active_boundaries() -> dict:
    """Returns the 4 boundary values for the currently active boundary set."""
    data = _read_tolerances()
    active = data.get('active_boundary_set', 'Default')
    return _get_boundary_sets(data).get(active, DEFAULT_BOUNDARIES)


def get_all_boundary_sets() -> list:
    """Returns a list of all named boundary set names."""
    data = _read_tolerances()
    return list(_get_boundary_sets(data).keys())


def get_all_boundary_sets_full() -> list:
    """Returns all boundary sets as a 2D list: [name, x_min, x_max, y_min, y_max]"""
    data = _read_tolerances()
    sets = _get_boundary_sets(data)
    return [
        [name, values['x_min'], values['x_max'], values['y_min'], values['y_max']]
        for name, values in sets.items()
    ]


def save_boundary_set(name: str, x_min: float, x_max: float, y_min: float, y_max: float) -> None:
    """Creates or updates a named boundary set."""
    data = _read_tolerances()
    if 'boundary_sets' not in data:
        data['boundary_sets'] = {'Default': DEFAULT_BOUNDARIES}
    data['boundary_sets'][name] = {
        'x_min': x_min, 'x_max': x_max,
        'y_min': y_min, 'y_max': y_max
    }
    _write_tolerances(data)


def set_active_boundary_set(name: str) -> None:
    """Sets the active boundary set by name."""
    data = _read_tolerances()
    if name in _get_boundary_sets(data):
        data['active_boundary_set'] = name
        _write_tolerances(data)


def delete_boundary_set(name: str) -> bool:
    """Deletes a named boundary set. Returns True if deleted, False if not found or is Default."""
    if name == 'Default':
        return False
    data = _read_tolerances()
    if name not in _get_boundary_sets(data):
        return False
    del data['boundary_sets'][name]
    if data.get('active_boundary_set') == name:
        data['active_boundary_set'] = 'Default'
    _write_tolerances(data)
    return True


def extract_boundary_values():
    """Returns (x_min, x_max, y_min, y_max) for the active boundary set."""
    active = get_active_boundaries()
    return (
        float(active.get('x_min', 10)),
        float(active.get('x_max', 300000)),
        float(active.get('y_min', 10)),
        float(active.get('y_max', 300000))
    )
