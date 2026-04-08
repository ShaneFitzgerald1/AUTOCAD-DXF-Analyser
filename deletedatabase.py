import os
import sys

def reset_database():
    # Delete user db
    app_data = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'MJHInterface')
    user_db = os.path.join(app_data, 'objectdatabase.db')
    if os.path.exists(user_db):
        os.remove(user_db)
        print(f"Deleted user db: {user_db}")
    else:
        print(f"User db not found at: {user_db}")

    # Delete bundled db
    this_dir = os.path.dirname(os.path.abspath(__file__))
    bundled_db = os.path.normpath(os.path.join(this_dir, 'objectdatabase.db'))

    if os.path.exists(bundled_db):
        os.remove(bundled_db)
        print(f"Deleted bundled db: {bundled_db}")
    else:
        print(f"Bundled db not found at: {bundled_db}")

if __name__ == '__main__':
    reset_database()