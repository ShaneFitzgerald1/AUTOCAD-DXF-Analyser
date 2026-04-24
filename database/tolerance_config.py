import os
import json

TOLERANCE_PATH = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'MJHInterface', 'tolerances.json')

DEFAULT_TOLERANCES = {
    'block_tolerance': 1,
    'line_tolerance_1': 1,
    'line_tolerance_2': 35
}


def _read_tolerances() -> dict:
    """Returns the full tolerances dict from the json file, or default structure if missing/corrupt."""
    if os.path.exists(TOLERANCE_PATH):
        try:
            with open(TOLERANCE_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {'active_set': 'Default', 'sets': {'Default': DEFAULT_TOLERANCES}}


def _write_tolerances(data: dict) -> None:
    """Writes the full tolerances dict to file."""
    os.makedirs(os.path.dirname(TOLERANCE_PATH), exist_ok=True)
    with open(TOLERANCE_PATH, 'w') as f:
        json.dump(data, f, indent=4)


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


def save_tolerance_set(name: str, block_tol: float, line_tol1: float, line_tol2: float) -> None: #used
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


def get_all_tolerance_sets_full() -> list:  #used 
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




