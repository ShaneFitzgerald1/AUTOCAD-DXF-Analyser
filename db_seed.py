
import os
from database.db_models import Session, ObjectID, CategoryLineRule

#if there is a line mistake it won't fail due to this database if it meets all criteria, however it will fail due to the category database


objects_data = [
    {'name': 'CPSHS100X100X8',     'type': 'INSERT', 'category': 'CP',     'on_channel_outline': 'Yes'},
    {'name': 'CPSHS120X120X6',     'type': 'INSERT', 'category': 'CP',     'on_channel_outline': 'Yes'},
    {'name': 'CPSHS120X120X6-B',   'type': 'INSERT', 'category': 'CP',     'on_channel_outline': 'Yes'},
    {'name': 'CPSHS150X50X8',      'type': 'INSERT', 'category': 'CP',     'on_channel_outline': 'Yes'},
    {'name': 'CPSHS150X50X8-B',    'type': 'INSERT', 'category': 'CP',     'on_channel_outline': 'Yes'},
    {'name': 'CPSHS160X160X16',    'type': 'INSERT', 'category': 'CP',     'on_channel_outline': 'Yes'},
    {'name': 'CPSHS160X160X16-B',  'type': 'INSERT', 'category': 'CP',     'on_channel_outline': 'Yes'},
    {'name': 'CPSHS180X180X16',    'type': 'INSERT', 'category': 'CP',     'on_channel_outline': 'Yes'},
    {'name': 'CPSHS180X180X16-B',  'type': 'INSERT', 'category': 'CP',     'on_channel_outline': 'Yes'},
    {'name': 'CPSHS150X50X8-L',    'type': 'INSERT', 'category': 'CP',     'on_channel_outline': 'Yes'},
    {'name': 'CPSHS150X50X8-PLATE','type': 'INSERT', 'category': 'CP',     'on_channel_outline': 'Yes'},
    {'name': 'CPRHS140X120X12.5',  'type': 'INSERT', 'category': 'CP',     'on_channel_outline': 'Yes'},
    {'name': 'CPSHS150x150x8','type': 'INSERT', 'category': 'CP',     'on_channel_outline': 'Yes'},
    {'name': 'CPSHS150x150x8-B',  'type': 'INSERT', 'category': 'CP',     'on_channel_outline': 'Yes'},
    {'name': 'CPSHS150x150x8-L',  'type': 'INSERT', 'category': 'CP',     'on_channel_outline': 'Yes'},

    {'name': 'NLB 30 CENTRE',      'type': 'INSERT', 'category': 'STUD',   'on_channel_outline': 'Yes'},
    {'name': 'NLB 25 CENTRE',      'type': 'INSERT', 'category': 'STUD',   'on_channel_outline': 'Yes'},
    {'name': 'NLB 50 CENTRE',      'type': 'INSERT', 'category': 'STUD',   'on_channel_outline': 'Yes'},
    {'name': 'NLB 60 CENTRE',      'type': 'INSERT', 'category': 'STUD',   'on_channel_outline': 'Yes'},
    {'name': 'NLB CORNER 50',      'type': 'INSERT', 'category': 'STUD',   'on_channel_outline': 'Yes'},
    {'name': 'NLB CORNER 60',      'type': 'INSERT', 'category': 'STUD',   'on_channel_outline': 'Yes'},

    {'name': 'MV01',               'type': 'INSERT', 'category': 'CONN',   'on_channel_outline': 'Yes'},
    {'name': 'SF01-150-A',         'type': 'INSERT', 'category': 'CONN',   'on_channel_outline': 'Yes'},
    {'name': 'SF01-150-B',         'type': 'INSERT', 'category': 'CONN',   'on_channel_outline': 'Yes'},
    {'name': 'SF01-180-A',         'type': 'INSERT', 'category': 'CONN',   'on_channel_outline': 'Yes'},
    {'name': 'SF01-180-N',         'type': 'INSERT', 'category': 'CONN',   'on_channel_outline': 'Yes'},
    {'name': 'SF01-150-N',         'type': 'INSERT', 'category': 'CONN',   'on_channel_outline': 'Yes'},
    {'name': 'SF03-150-A',         'type': 'INSERT', 'category': 'CONN',   'on_channel_outline': 'Yes'},
    {'name': 'SF03-150-N',         'type': 'INSERT', 'category': 'CONN',   'on_channel_outline': 'Yes'},
    {'name': 'SF03-180-A',         'type': 'INSERT', 'category': 'CONN',   'on_channel_outline': 'Yes'},
    {'name': 'SF03-180-N',         'type': 'INSERT', 'category': 'CONN',   'on_channel_outline': 'Yes'},
    {'name': 'SF-15',              'type': 'INSERT', 'category': 'CONN',   'on_channel_outline': 'Yes'},
    {'name': 'SF-15-OPP',          'type': 'INSERT', 'category': 'CONN',   'on_channel_outline': 'Yes'},
    {'name': 'VT1',                'type': 'INSERT', 'category': 'CONN',   'on_channel_outline': 'Yes'},
    {'name': 'MV02',               'type': 'INSERT', 'category': 'CONN',   'on_channel_outline': 'Yes'},
    {'name': 'SF-16',              'type': 'INSERT', 'category': 'CONN',   'on_channel_outline': 'Yes'},

    {'name': 'B1',                 'type': 'INSERT', 'category': 'OTHER',  'on_channel_outline': 'Yes'},
    {'name': 'B2',                 'type': 'INSERT', 'category': 'OTHER',  'on_channel_outline': 'Yes'},
    {'name': 'B3',                 'type': 'INSERT', 'category': 'OTHER',  'on_channel_outline': 'Yes'},
    {'name': 'B4',                 'type': 'INSERT', 'category': 'OTHER',  'on_channel_outline': 'Yes'},
    {'name': 'B5',                 'type': 'INSERT', 'category': 'OTHER',  'on_channel_outline': 'Yes'},
    {'name': 'B6',                 'type': 'INSERT', 'category': 'OTHER',  'on_channel_outline': 'Yes'},
    {'name': 'LP',                 'type': 'INSERT', 'category': 'OTHER',  'on_channel_outline': 'Yes'},
    {'name': 'NP',                 'type': 'INSERT', 'category': 'OTHER',  'on_channel_outline': 'Yes'},
    {'name': 'TRUSS VERTICAL',     'type': 'INSERT', 'category': 'OTHER',  'on_channel_outline': 'No'},
    {'name': 'RESTRAINT',          'type': 'INSERT', 'category': 'OTHER',  'on_channel_outline': 'Yes'},
    {'name': 'STIFFENER',          'type': 'INSERT', 'category': 'OTHER',  'on_channel_outline': 'Yes'},
    {'name': 'COUPLER',            'type': 'INSERT', 'category': 'OTHER',  'on_channel_outline': 'Yes'},

    {'name': 'WINDOW 1',           'type': 'INSERT', 'category': 'WINDOW', 'on_channel_outline': 'Yes'},
    {'name': 'WINDOW 2',           'type': 'INSERT', 'category': 'WINDOW', 'on_channel_outline': 'Yes'},
    {'name': 'WINDOW 3',           'type': 'INSERT', 'category': 'WINDOW', 'on_channel_outline': 'Yes'},
    {'name': 'WINDOW 4',           'type': 'INSERT', 'category': 'WINDOW', 'on_channel_outline': 'Yes'},
    {'name': 'WINDOW 5',           'type': 'INSERT', 'category': 'WINDOW', 'on_channel_outline': 'Yes'},

    {'name': 'CENTER',             'type': 'INSERT', 'category': 'WP',     'on_channel_outline': 'Yes'},
    {'name': 'CORNER',             'type': 'INSERT', 'category': 'WP',     'on_channel_outline': 'Yes'},
    {'name': 'LEFT',               'type': 'INSERT', 'category': 'WP',     'on_channel_outline': 'Yes'},
    {'name': 'RIGHT',              'type': 'INSERT', 'category': 'WP',     'on_channel_outline': 'Yes'},
    {'name': 'NLB CENTER',         'type': 'INSERT', 'category': 'WP',     'on_channel_outline': 'Yes'},
    {'name': 'NLB LEFT',           'type': 'INSERT', 'category': 'WP',     'on_channel_outline': 'Yes'},
    {'name': 'NLB RIGHT',          'type': 'INSERT', 'category': 'WP',     'on_channel_outline': 'Yes'},
    {'name': 'NARROW LEFT',        'type': 'INSERT', 'category': 'WP',     'on_channel_outline': 'Yes'},
    {'name': 'NARROW RIGHT',       'type': 'INSERT', 'category': 'WP',     'on_channel_outline': 'Yes'},
    {'name': 'DEFINITE NARROW LEFT','type': 'INSERT','category': 'WP',     'on_channel_outline': 'Yes'},
    {'name': 'DEFINITE NARROW RIGHT','type':'INSERT','category': 'WP',     'on_channel_outline': 'Yes'},
    {'name': 'CORNER-M',           'type': 'INSERT', 'category': 'WP',     'on_channel_outline': 'Yes'},

    {'name': '535 TRUSS LINE',     'type': 'LINE',   'category': 'TRUSS LINE',  'on_channel_outline': 'No'},
    {'name': '460 TRUSS LINE',     'type': 'LINE',   'category': 'TRUSS LINE',  'on_channel_outline': 'No'},
    {'name': '475 TRUSS LINE',     'type': 'LINE',   'category': 'TRUSS LINE',  'on_channel_outline': 'No'},
    {'name': '275 TRUSS LINE',     'type': 'LINE',   'category': 'TRUSS LINE',  'on_channel_outline': 'No'},
    {'name': 'TRUSS BRACING',      'type': 'LINE',   'category': 'TRUSS BRACING',  'on_channel_outline': 'No'},
    {'name': '325 TRUSS LINE',     'type': 'LINE',   'category': 'TRUSS LINE',  'on_channel_outline': 'No'},
    {'name': '225 TRUSS LINE',     'type': 'LINE',   'category': 'TRUSS LINE',  'on_channel_outline': 'No'},
    {'name': '315 TRUSS LINE',     'type': 'LINE',   'category': 'TRUSS LINE',  'on_channel_outline': 'No'},
    {'name': '215 TRUSS LINE',     'type': 'LINE',   'category': 'TRUSS LINE',  'on_channel_outline': 'No'},
    {'name': '205 TRUSS LINE',     'type': 'LINE',   'category': 'TRUSS LINE',  'on_channel_outline': 'No'},
    {'name': '305 TRUSS LINE',     'type': 'LINE',   'category': 'TRUSS LINE',  'on_channel_outline': 'No'},
    {'name': '60 SHS TRUSS LINE',  'type': 'LINE',   'category': 'SHS TRUSS LINE',  'on_channel_outline': 'No'},

    {'name': '80 HEADER',          'type': 'LINE',   'category': 'HEADER', 'on_channel_outline': 'Yes'},
    {'name': '60 HEADER',          'type': 'LINE',   'category': 'HEADER', 'on_channel_outline': 'Yes'},
    {'name': '40 HEADER',          'type': 'LINE',   'category': 'HEADER', 'on_channel_outline': 'Yes'},

    {'name': '350 CILL',           'type': 'LINE',   'category': 'CILL LINE',  'on_channel_outline': 'Yes'},
    {'name': 'WALL',               'type': 'LINE',   'category': 'WALL LINE',  'on_channel_outline': 'Yes'},

    {'name': 'DIAGONAL BRACE',     'type': 'LINE',   'category': 'BRACE LINE',  'on_channel_outline': 'Yes'},
    {'name': 'Door',               'type': 'LWPOLYLINE', 'category': None, 'on_channel_outline': 'No'},
    {'name': 'CHANNEL OUTLINE',    'type': 'LWPOLYLINE', 'category': 'CHANNEL OUTLINE', 'on_channel_outline': 'Yes'},
    {'name': 'FLOOR BEAM',    'type': 'LINE', 'category': 'FLOOR', 'on_channel_outline': 'No'},
    {'name': 'COMPOUND',    'type': 'LINE', 'category': 'COMPOUND LINE', 'on_channel_outline': 'Yes'}
    ]



def seed_database():
    session = Session()
    try:
        existing_count = session.query(ObjectID).count()
        if existing_count > 0:
            print(f"Database already has {existing_count} objects. Skipping seed to avoid duplicates.")
            print("If you want to re-seed, clear the objects table first.")
            return

        objects = [ObjectID(**data) for data in objects_data]
        session.add_all(objects)
        session.commit()
        print(f"Successfully seeded {len(objects)} objects into the database.")
    except Exception as e:
        session.rollback()
        print(f"Seeding failed: {e}")
        raise
    finally:
        session.close()



category_line_data = [
    {'category': 'TRUSS LINE' , 'allowed_connections' : ('TRUSS LINE' , 'HEADER', 'WALL LINE', 'CILL LINE', 'BRACE LINE', 'SHS TRUSS LINE', 'CHANNEL OUTLINE', 'STUD', 'OTHER'), 'double_connection': 'No', 'on_channel': 'No'}, 
    {'category': 'TRUSS BRACING', 'allowed_connections': ('TRUSS LINE' , 'HEADER', 'WALL LINE', 'CILL LINE', 'BRACE LINE', 'SHS TRUSS LINE', 'CHANNEL OUTLINE'), 'double_connection': 'Yes', 'on_channel': 'No'},
    {'category': 'SHS TRUSS LINE', 'allowed_connections': ('TRUSS LINE' , 'HEADER', 'WALL LINE', 'CILL LINE', 'BRACE LINE', 'SHS TRUSS LINE', 'CHANNEL OUTLINE'), 'double_connection': 'No', 'on_channel': 'No'},
    {'category': 'HEADER', 'allowed_connections': ('CP', 'STUD'), 'double_connection': 'Yes', 'on_channel': 'Yes'},
    {'category': 'CILL LINE', 'allowed_connections': ('STUD','OTHER'), 'double_connection': 'Yes', 'on_channel': 'Yes' },
    {'category': 'WALL LINE', 'allowed_connections': ('CP', 'STUD'), 'double_connection': 'Yes', 'on_channel': 'Yes' },
    {'category': 'BRACE LINE', 'allowed_connections': ('CP', 'STUD'), 'double_connection': 'Yes', 'on_channel': 'Yes'},  
    {'category': 'FLOOR', 'allowed_connections': ('CP', 'STUD', 'HEADER', 'BRACE LINE', 'CILL LINE', 'WALL LINE', 'CHANNEL OUTLINE'), 'double_connection': 'Yes', 'on_channel': 'No'}, 
    {'category': 'CHANNEL OUTLINE', 'allowed_connections': ('TRUSS LINE' , 'TRUSS BRACING', 'HEADER', 'WALL LINE', 'CILL LINE', 'BRACE LINE', 'SHS TRUSS LINE', 'FLOOR'), 'double_connection': 'Yes', 'on_channel': 'Yes'}, 
    {'category': 'COMPOUND LINE', 'allowed_connections': ('CP'), 'double_connection': 'Yes', 'on_channel': 'Yes'}
]




def seed_category_line_rules():
    session = Session()
    try:
        existing_count = session.query(CategoryLineRule).count()
        if existing_count > 0:
            print(f"Category rules already seeded ({existing_count} rows). Skipping.")
            return

        rules = []
        for item in category_line_data:
            conn = item['allowed_connections']
            if isinstance(conn, tuple):
                conn = ','.join(conn)
            rules.append(CategoryLineRule(
                category=item['category'],
                allowed_connections=conn,
                double_connection=item['double_connection'],
                on_channel=item['on_channel']
            ))

        session.add_all(rules)
        session.commit()
        print(f"Successfully seeded {len(rules)} category line rules.")
    except Exception as e:
        session.rollback()
        print(f"Seeding failed: {e}")
        raise
    finally:
        session.close()




if __name__ == '__main__':
    seed_database()
    seed_category_line_rules()

    import shutil
    src = os.path.join(os.environ.get('APPDATA', ''), 'MJHInterface', 'objectdatabase.db')
    dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'objectdatabase.db')
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"Copied database to project root: {dst}")





#createdb -U postgres objectdatabase 

#createdb -U postgres categorydatabase 


# psql -U postgres -c "CREATE DATABASE objectdatabase;"


# psql -U postgres -c "CREATE DATABASE categorydatabase;"

# Run the code 

#psql -U postgres --dbname objectdatabase
#SELECT * FROM people 

#psql -U postgres
#DROP DATABASE objectdatabase;


#categorydatabase

#psql -U postgres -l