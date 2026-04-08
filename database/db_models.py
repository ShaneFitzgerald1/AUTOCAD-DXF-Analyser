import sys
import os
import shutil
import json
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class ObjectID(Base):
    __tablename__ = 'objects'
    object_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    category = Column(String)
    on_channel_outline = Column(String)

class CategoryLineRule(Base):
    __tablename__ = 'category_line_rules'
    id = Column(Integer, primary_key=True)
    category = Column(String, nullable=False)
    allowed_connections = Column(String)
    double_connection = Column(String, nullable=False)
    on_channel = Column(String)

CONFIG_PATH = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'MJHInterface', 'config.json')
#above builds the filepath to config.json
#config.json is a small text file to remember users database choice between sessions. 
#building a reliable path to a folder where the app can store its settings

def get_configured_db_path():
    """Returns the DB path saved in config.json, or None if not set.
    Function checks if config.json exists at CONFIG_PATH"""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f).get('db_path')
        except Exception:
            pass
    return None

def save_configured_db_path(path):
    """Saves the chosen DB path to config.json."""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True) #checks that the folder exists 
    with open(CONFIG_PATH, 'w') as f: #opens file at the path, w overwrites any previous data, f is the variable for file
        json.dump({'db_path': path}, f) #actually writes db_path into file 

def get_db_path():
    app_data = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'MJHInterface')
    os.makedirs(app_data, exist_ok=True)

    # When packaged, use the path from config.json if one has been saved
    if getattr(sys, 'frozen', False):
        configured = get_configured_db_path()
        if configured and os.path.exists(configured):
            return configured

    # Packaged app: db lives in _internal next to the exe
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), '_internal', 'objectdatabase.db')

    # Dev (VS Code): db lives at the project root
    dev_db = os.path.join(os.path.dirname(__file__), '..', 'objectdatabase.db') #if we are in vs code open the seeded database 
    return dev_db

class _DynamicSession:
    """Proxy so all existing Session() calls always use the current engine,
    even after reinitialise_db() swaps it out at runtime."""
    _factory = None
    def __call__(self, *args, **kwargs):
        return self._factory(*args, **kwargs)

Session = _DynamicSession()

def _init_engine(path):
    global engine
    engine = create_engine(f'sqlite:///{path}', echo=False)
    Base.metadata.create_all(engine)
    Session._factory = sessionmaker(bind=engine)

def reinitialise_db(path):
    """Switch the active database to path without restarting the app."""
    save_configured_db_path(path)
    _init_engine(path)

_init_engine(get_db_path())