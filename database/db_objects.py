from database.db_models import Session, ObjectID, CategoryLineRule
from backend.mathematical import Mathematical
maths = Mathematical()

def get_catalogue():

    objects = []
    session = Session()
    try:
        all_objects = session.query(ObjectID).all()
        for obj in all_objects:
            objects.append([obj.name, obj.type, obj.category, obj.on_channel_outline ])
        return objects
    except Exception as e:
        print(f"Warning: Could not load catalogue from database: {e}")
        return [] 
    finally:
        session.close()

def get_category_catalogue(): 

    categories = []
    session = Session() 
    try:
        all_categories = session.query(CategoryLineRule).all()
        for cat in all_categories:
            categories.append([cat.category, cat.allowed_connections, cat.double_connection, cat.on_channel])
        return categories
    
    except Exception as e:
        print(f"Warning: Could not load catalogue from database: {e}")
        return [] 
    finally:
        session.close()   

# categories = get_category_catalogue() 
# print(f'These are the categories {categories}')

       


def name_match_block(blockrefs, lines, actual_type, wall_slopes, wall_intercepts, all_walls, line_refs): 
    blocks = maths.Channel_check_block(wall_slopes, wall_intercepts, blockrefs)

    _, _, _, _, lines_cl = maths.Chanel_check_line(wall_slopes, wall_intercepts, lines, all_walls, line_refs)
    objects = get_catalogue()
    accepted_block_names = []
    rejected_block_names = []
    accepted_line_names = []
    rejected_line_names = []
    blockname_unmatched = []
    linename_unmatched = []


    # Build lookup lists from catalogue
    valid_insert_names = []
    valid_line_names = []


    # print(f'Amount of objects {len(objects)}')

    for object in objects:
        name, type, category, on_channel_outline = object
        if type not in ('LINE', 'LWPOLYLINE'):
            valid_insert_names.append((name, on_channel_outline))
        if type not in ('INSERT', 'LWPOLYLINE'):
            valid_line_names.append((name, on_channel_outline))

    
    if actual_type == 'INSERT':
        for block in blocks:
            actual_name, x, y, _, on_channel = block
            name_matched = False
            channel_verification = False

            for name, on_channel_outline in valid_insert_names:
                if actual_name.upper() == name.upper():
                    name_matched = True
                    if on_channel == 'Yes' and on_channel_outline == 'Yes':
                        channel_verification = True
                    if on_channel == 'No' and on_channel_outline == 'No':
                        channel_verification = True
                    break

            if name_matched and channel_verification:
                accepted_block_names.append(actual_name)
            if name_matched and not channel_verification:
                rejected_block_names.append([actual_name, x, y, 'Block rejected due to unexpected position'])
            if not name_matched and channel_verification:
                rejected_block_names.append([actual_name, x, y, 'Block has unexpected name'])
            if not name_matched and not channel_verification:
                rejected_block_names.append([actual_name, x, y, 'Block rejected due to unexpected position and name'])
            if not name_matched:
                blockname_unmatched.append(actual_name)

        return accepted_block_names, rejected_block_names, blockname_unmatched

    if actual_type == 'LINE':
        for line in lines_cl:
            actual_l_name, x_s, y_s, x_e, y_e, on_channel = line
            line_name_matched = False
            channel_verified = False

            for name, on_channel_outline in valid_line_names:
                if actual_l_name.upper() == name.upper():
                    line_name_matched = True  
                elif 'TRUSS LINE' in actual_l_name.upper():
                    parts = actual_l_name.upper().split()
                    if parts[0].isdigit() and 100 <= int(parts[0]) <= 999:
                        line_name_matched = True
        
                if on_channel == 'Yes' and on_channel_outline == 'Yes':
                    channel_verified = True
                if on_channel == 'No' and on_channel_outline == 'No':
                    channel_verified = True

                if line_name_matched: 
                    break 

            if line_name_matched and channel_verified:
                accepted_line_names.append(actual_l_name)
            if line_name_matched and not channel_verified:
                rejected_line_names.append([actual_l_name, x_s, y_s, x_e, y_e, 'Line rejected due to not being in expected position'])
            if not line_name_matched and not channel_verified:
                rejected_line_names.append([actual_l_name, x_s, y_s, x_e, y_e, f'Line rejected: {actual_l_name} is not present in the DataBase'])
            if not line_name_matched:
                rejected_line_names.append([actual_l_name, x_s, y_s, x_e, y_e, f'Line rejected: {actual_l_name} is not present in the DataBase'])
                linename_unmatched.append(actual_l_name)
 
        return accepted_line_names, rejected_line_names, linename_unmatched
    

def before_after(fixed_all_blocks, blockrefs, lines, correct_lines, fixed_lines, wall_slopes, wall_intercepts, all_walls, line_refs):
        
    # correct_lines.extend(fixed_lines)
    all_correct_lines = correct_lines + fixed_lines

    sort_blockrefs = []
    
    #If a block is inside a bedit, we know this and how to fix the problem, database would reject outer block name
    # this would be a pointless rejection as we have already identified the issue, so we compare the blockname inside the bedit to the database 
    # i.e. we compare the actual block name to the database 
    for block in blockrefs: #sorting blockrefs 
        name, x, y, angle, name_error = block 
        if name_error is not None: 
            sort_blockrefs.append([name_error, x, y, angle, name])
        else:
            sort_blockrefs.append([name, x, y, angle, name_error])    

    #All accepted and rejected blocks post check, if an error arised here this is a big issue
    post_accepted_block, post_rejected_block, blockname_unmatched = name_match_block(fixed_all_blocks, all_correct_lines, 'INSERT', wall_slopes, wall_intercepts, all_walls, line_refs)
    post_accepted_line, post_rejected_lines, linename_unmatched = name_match_block(fixed_all_blocks, all_correct_lines, 'LINE', wall_slopes, wall_intercepts, all_walls, line_refs)


    return post_accepted_block, post_accepted_line, post_rejected_block, post_rejected_lines, blockname_unmatched, linename_unmatched



def categories_sorter(line_connections): 
    category_list = [] 

    for line in line_connections: 
        line_name, line_start_entity, line_end_entity, x_start, y_start, x_end, y_end = line 

        line_category = get_category(line_name)
        line_start_category = get_category(line_start_entity)
        line_end_category = get_category(line_end_entity)

        category_list.append([line_name, line_category, line_start_category, line_end_category, x_start, y_start, x_end, y_end])
    return category_list     

    
def get_category(line_name): 
    """Function that puts each line name into a category based on its name"""
    objects = get_catalogue()
    if line_name is None: 
        return None 
    for object in objects: 
        object_name, type, category, on_channel_outline = object 
        if line_name.upper() == object_name.upper(): 
            return category 
    
    if 'TRUSS LINE' in line_name.upper():
            parts = line_name.upper().split()
            if parts[0].isdigit() and 100 <= int(parts[0]) <= 999:
                return 'TRUSS LINE'
                
    return None 


def validate_categories(line_line_connections, line_block_connections):
    categories = get_category_catalogue() 

    ll_connections = categories_sorter(line_line_connections)
    lb_connections = categories_sorter(line_block_connections)
    all_connections = ll_connections + lb_connections

    correct_connections_cat = []
    mand_fail = []
    quantity_fail = []
    both_fail = []

    for line in all_connections: 
        line_name, line_category, line_start_category, line_end_category, x_start, y_start, x_end, y_end = line #lines being checked 
        safe_connections = False 
        safe_connections_start = False 
        safe_connections_end = False 
        untrue_quantity_connections = False 

        for categor in categories: #the category database being called 
            cat, allowed_connections, double_connection, on_channel = categor

            if allowed_connections:
                allowed_list = [a.strip() for a in allowed_connections.split(',')]
            else:
                allowed_list = [] 

            if cat == line_category: 
                if line_start_category in allowed_list and line_end_category in allowed_list:  
                    safe_connections = True 
                    safe_connections_start = True 
                    safe_connections_end = True 
                
                if line_category == 'TRUSS LINE': 
                    if line_start_category is None or line_end_category is None: 
                        safe_connections_start = True
                        safe_connections_end = True   
                    if line_start_category == 'TRUSS BRACING' or line_end_category == 'TRUSS BRACING': 
                        safe_connections_start = True 
                        safe_connections_end = True 
                    if line_start_category == 'TRUSS BRACING' and line_end_category == 'TRUSS BRACING': 
                        safe_connections_start = False   
                        safe_connections_end = False 

                if line_category == 'SHS TRUSS LINE': 
                    if line_start_category is None or line_end_category is None: 
                        safe_connections_start = True        
                        safe_connections_end = True   

                if double_connection == 'Yes': 
                    if line_category == 'TRUSS LINE' or line_category == 'SHS TRUSS LINE': 
                        continue 
                    if line_start_category is None or line_end_category is None: 
                        untrue_quantity_connections = True 

                if double_connection == 'No':  #future proofing, if something doesnt have two connections, code will allow for this
                    if line_start_category is None and line_end_category is not None: 
                        safe_connections_start = True 
                        safe_connections_end = True 
                        untrue_quantity_connections = False 
                    if line_start_category is not None and line_end_category is None: 
                        safe_connections_start = True 
                        safe_connections_end = True 
                        untrue_quantity_connections = False 

                if cat == 'BRACE LINE':  #brace lines may fall short of studs 
                    if (line_start_category == 'CP') and line_end_category is None:
                        safe_connections_start = True 
                        safe_connections_end = True 
                        untrue_quantity_connections = False 
                    if (line_end_category == 'CP') and line_start_category is None: 
                        safe_connections_start = True 
                        safe_connections_end = True       
                        untrue_quantity_connections = False       
       

        if safe_connections_start and safe_connections_end and not untrue_quantity_connections: 
            correct_connections_cat.append([line_name])  
        if not safe_connections_start and safe_connections_end and not untrue_quantity_connections: 
            mand_fail.append([line_name, x_start, y_start, line_start_category, x_end, y_end, line_end_category, f'{line_name} start is at/on an incorrect line, object, or position.'])
        if safe_connections_start and not safe_connections_end and not untrue_quantity_connections: 
            mand_fail.append([line_name, x_start, y_start, line_start_category, x_end, y_end, line_end_category, f'{line_name} end is at/on an incorrect line, object, or position.'])   
        if not safe_connections_start and not safe_connections_end and not untrue_quantity_connections: 
            mand_fail.append([line_name, x_start, y_start, line_start_category, x_end, y_end, line_end_category, f'{line_name} start and end is at/on an incorrect line, object, or position.'])   


        if safe_connections_start and safe_connections_end and untrue_quantity_connections: 
            quantity_fail.append([line_name, x_start, y_start, line_start_category, x_end, y_end, line_end_category, f'{line_name} must end on the specified object.'])
            
        if not safe_connections_start and safe_connections_end and untrue_quantity_connections: 
            both_fail.append([line_name, x_start, y_start, line_start_category, x_end, y_end, line_end_category, f'{line_name} start is incorrect or does not end on the required object.'])
        if safe_connections_start and not safe_connections_end and untrue_quantity_connections: 
            both_fail.append([line_name, x_start, y_start, line_start_category, x_end, y_end, line_end_category, f'{line_name} end is incorrect or does not end on the required object.'])
        if not safe_connections_start and not safe_connections_end and untrue_quantity_connections: 
            both_fail.append([line_name, x_start, y_start, line_start_category, x_end, y_end, line_end_category, f'{line_name} start and end is incorrect or does not end on the required object.'])
       
    all_fail_cat = mand_fail + quantity_fail + both_fail 

    return correct_connections_cat, all_fail_cat

def dxf_mistake_block_explained(mistake_exp): 
    categories = get_category_catalogue() 
    mistake_block_reason = []

    # for db_category in categories: 

    for block in mistake_exp:
        name, x, y, line_name, name_error, mistake = block 
         
        if line_name is None: 
            mistake_block_reason.append([name, x, y, f'{name} is not near any line'])

        if name_error and not mistake: 
            mistake_block_reason.append([name, x, y, f'{name} is inside a BEDIT' ])    

        else:   
            category = get_category(line_name)

            for db_categories in categories: 
                db_category, allowed_connections, double_connection, on_channel = db_categories

                if name_error and mistake: 
                    if db_category == category: 
                        if on_channel == 'Yes': 
                            mistake_block_reason.append([name, x, y, f'{name} is not on the Channel Outline'])
                        if on_channel == 'No':
                            mistake_block_reason.append([name, x, y, f'{name} is not on {line_name}'])    
                if not name_error and mistake: 
                    if db_category == category: 
                        if on_channel == 'Yes': 
                            mistake_block_reason.append([name, x, y, f'{name} is not on the Channel Outline'])
                        if on_channel == 'No':
                            mistake_block_reason.append([name, x, y, f'{name} is not on {line_name}'])    
    return mistake_block_reason       

def dxf_mistake_line_explained(line_mistake_explain): 
    """This is a function identifies where errors occured in lines and the reason why
    it checks the points it starts and ends on to see if it falls short of a line or goes past it"""
    categories = get_category_catalogue() 

    mistake_line_reason = []
    for line in line_mistake_explain: 
        (name, x_start, y_start, x_end, y_end, new_x_start,
                        new_y_start, new_x_end, new_y_end, line_start_name, line_end_name) = line 
        
        on_channel_outline = False 
        gone_past_line = False 
        short_of_line = False 
        
        #Situation 1 the mistake is at the end point 
        if abs(x_start - new_x_start) < 1 and abs(y_start - new_y_start) < 1: #if hte mistake is not at the start point 
            category = get_category(line_end_name)
            for db_categories in categories: 
                db_category, allowed_connections, double_connection, on_channel = db_categories
                if category == db_category: 
                    if on_channel == 'Yes': 
                        on_channel_outline = True 

                    if ((x_end > new_x_end and x_end > x_start) or (y_end > new_y_end and y_end > y_start) or
                        (x_end < new_x_end and x_end < x_start) or (y_end < new_y_end and y_end < y_start )): #if line goes past the line it should connect to
                        gone_past_line = True   
                    
                    #if line falls short of line it should connect to 
                    if ((new_x_end > x_end and x_end > x_start) or (new_y_end > y_end and y_end > y_start) or 
                        (new_x_end < x_end and x_start > x_end) or (new_y_end < y_end and y_start > y_end)):  
                        short_of_line = True    

            if on_channel_outline and gone_past_line: 
                mistake_line_reason.append([name, new_x_end, new_y_end, f'{name} has gone past the Channel Outline'])    
            if on_channel_outline and short_of_line: 
                mistake_line_reason.append([name, new_x_end, new_y_end, f'{name} has fallen short of the Channel Outline'])
            if not on_channel_outline and gone_past_line: 
                mistake_line_reason.append([name, new_x_end, new_y_end, f'{name} has gone past {line_end_name}'])    
            if not on_channel_outline and short_of_line: 
                mistake_line_reason.append([name, new_x_end, new_y_end, f'{name} has fallen short of {line_end_name}'])   

        #Situation 2 the mistake is at the start point
        if abs(x_end - new_x_end) < 1 and abs(y_end - new_y_end) < 1: 
            category = get_category(line_start_name)
            for db_categories in categories: 
                db_category, allowed_connections, double_connection, on_channel = db_categories
                if category == db_category: 
                    if on_channel == 'Yes': 
                        on_channel_outline = True     

                    if ((x_start > new_x_start and x_start > x_end) or (y_start > new_y_start and y_start > y_end) or
                        (x_start < new_x_start and x_start < x_end) or (y_start < new_y_start and y_start < y_end)): 
                        gone_past_line = True

                    if ((x_start < new_x_start and x_start > x_end) or (y_start < new_y_start and y_start > y_end) or
                        (x_start > new_x_start and x_start < x_end) or (y_start > new_y_start and y_start < y_end)):
                        short_of_line = True 

            if on_channel_outline and gone_past_line: 
                mistake_line_reason.append([name, new_x_start, new_y_start, f'{name} has gone past the Channel Outline'])    
            if on_channel_outline and short_of_line: 
                mistake_line_reason.append([name, new_x_start, new_y_start, f'{name} has fallen short of the Channel Outline'])
            if not on_channel_outline and gone_past_line: 
                mistake_line_reason.append([name, new_x_start, new_y_start, f'{name} has gone past {line_start_name}'])    
            if not on_channel_outline and short_of_line: 
                mistake_line_reason.append([name, new_x_start, new_y_start, f'{name} has fallen short of {line_start_name}'])                        

    return mistake_line_reason





