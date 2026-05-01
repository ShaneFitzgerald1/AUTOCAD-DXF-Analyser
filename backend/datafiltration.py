import math 
from backend.mathematical import Mathematical
from database.db_objects import get_catalogue
from database.tolerance_config import get_active_tolerances
from database.tolerance_config import extract_values_from_tolerance_sets

maths = Mathematical
class datafiltration: 
    """Datafiltration filters all the data extracted from the autocad, it locates and fixes any mistakes that may arise 
       Possible mistakes the class corrects inlcude: Block refernce errors, Blockrefernce name errors (inocorrect pasting of blocks when making files causes blocks inside blocks),
       Line placement errors and duplicate lines 
       The class contains six functions 
       remove_duplicate_lines: removes any duplicates and ensures there are no repeats of identical lines 
       On_Channel_Outline: Corrects block references that are not located on any lines
       filter_name_errors: flags blocks that have a name error as a mistake
       find_line_error: Locates any line errors 
       fix_line_error: Fixes any line errors 
       find_fixed_line_points: Finds exact points that mistakes occur within lines so they are flagged in corrected dxf """
    
    @staticmethod
    def flag_duplicate_lines(all_lines):
        seen = []
        line_duplicates = []
        
        for line in all_lines:
            name, x_start, y_start, x_end, y_end, offset, line_ref = line
            
            # Normalise direction so A->B and B->A are treated as the same line
            coords = tuple(sorted([(x_start, y_start), (x_end, y_end)]))
            key = (name, coords)
            
            if key in seen:
                line_duplicates.append([name, x_start, y_start, x_end, y_end, line_ref, f'{name} is a duplicate line'])
            else:
                seen.append(key)
     
        return line_duplicates
    
    @staticmethod
    def On_Channel_Line(filtered_blockref, filtered_walls, line_properties, bedit_check, tolerance1, tolerance2):
        """This function checks all block references to see if they are on a line. If Yes a Correct result is appended
           If blcoks are within lines to a certain degree their position is fixed to the line using minimum perpendicular distance to a line
           If there the block reference is near no lines an error is return 
           Function inputs: Filepath, Tolerence1 (if something is within this its not a mistake), Tolerence2 if it falls within this and outside T1 its a mistake """

        blocks_on_line= []
        mistake_points = []
        correct_blocks = []
        corrected_blocks = []
        mistake_exp = []

        # Use enumerate to get both index and block data
        for block in filtered_blockref:
            name, x, y, angle, name_error, block_ref = block 
         
            # Find the closest corner to this block
            closest_corner = None
            min_corner_dist = float('inf') #set the value intially to an infinitily large distance 
            
            for wall in filtered_walls: #defining the x and y wall points on channel outline 
                x_wall = wall[0]
                y_wall = wall[1]
                distance_corner = math.sqrt((x_wall - x)**2 + (y_wall - y)**2)
                
                if distance_corner < min_corner_dist:
                    min_corner_dist = distance_corner #set the corner distance found to the minimum corner distance 
                    closest_corner = (x_wall, y_wall)

            found_match = False
            
            #Situation 1: Check for exact matches (within tolerance)
            for i in range(len(line_properties)):
                line_name, slope, intercept, xs, ys, xe, ye = line_properties[i]
        
                # Case 1: Vertical line
                if slope is None:
                    x_intercept = float(intercept.split()[2]) #Pulling the float value out 
                    distance = abs(x - x_intercept)
                    
                    if distance <= tolerance1: #if the distance is less than the tolerance we've found a match, this logic applies to all cases 
                        blocks_on_line.append([name, x, y, angle, i, 'vertical', 'On Line', 'Exact'])  #store for interface table presentation 
                        correct_blocks.append([name, x, y, angle, name_error, block_ref])   #Store for creating new dxf 
                        found_match = True
                        break
                
                # Case 2: Normal line with slope
                else:
                    expected_y = slope * x + intercept
                    distance = abs(y - expected_y)

                    if distance <= tolerance1:
                        blocks_on_line.append([name, x, y, angle, i, 'normal', 'On Line', 'Exact'])
                        correct_blocks.append([name, x, y, angle, name_error, block_ref])
                        found_match = True
                        break
            
            #Situation 2: Look for near matches 
            if not found_match:
                for i in range(len(line_properties)):
                    line_name, slope, intercept, xs, ys, xe, ye = line_properties[i]
                    
                    #Blocks are being checked against the equation of lines of other lines, an equation of a line assumes a lines length is infinite throuhgh space
                    #the below code stops checking lines that are far from the block being checked to be corrected onto that line 
                    avoid_distant_lines = (xs <= x <= xe or xe <= x <= xs or ys <= y <= ye or ye <= y <= y)
                                
                    min_distance = min(abs(x - xs), abs(x - xe),   #find miniumum distance to the line if not within the range    
                        abs(y - ys), abs(y - ye))
                    
                    if not avoid_distant_lines and (min_distance > 5):  #if the block is not within the range of the line then check if it is within a tolerence, than skip that line
                        continue 

                    # Case 1: Vertical line
                    if slope is None:
                        x_intercept = float(intercept.split()[2])
                        distance = abs(x - x_intercept)
                        
                        if distance <= tolerance2:
                            blocks_on_line.append([name, x, y, angle, i, 'vertical', 'Near Line', 'Warning'])
                            
                            if min_corner_dist <= 5: #If its within 5 of a corner move the block reference to the nearest corner 
                                mistake_points.append([name, x, y, closest_corner[0], closest_corner[1], block_ref])   #Store for interface presnetaion 
                                corrected_blocks.append([name, closest_corner[0], closest_corner[1], angle, name_error, block_ref]) #Store for dxf
                                mistake_exp.append([name, x, y, line_name, name_error, block_ref]) #Using the corrected poins for now
                              
                            else:
                                mistake_points.append([name, x, y, x_intercept, y, block_ref])  #Store for Interface Presentation
                                corrected_blocks.append([name, x_intercept, y, angle, name_error, block_ref])   # Store for dxf 
                                mistake_exp.append([name, x, y, line_name, name_error, block_ref])
                            
                            found_match = True
                            break
                    
                    # Case 2: Normal line with slope, Holds same logic as above code 
                    else:
                        expected_y = slope * x + intercept
                        distance = abs(y - expected_y)
                        
                        if distance <= tolerance2:
                            blocks_on_line.append([name, x, y, angle, i, 'normal', 'Near Line', 'Warning'])
                            
                            if min_corner_dist <= tolerance2:
                                mistake_points.append([name, x, y, closest_corner[0], closest_corner[1], block_ref])
                                corrected_blocks.append([name, closest_corner[0], closest_corner[1], angle, name_error, block_ref])
                                mistake_exp.append([name, x, y, line_name, name_error, block_ref])
                               

                            else: #We have a Point and  a slope, the below finds the minimum perpendicular distance from the orignal point to that line
                                #The code returns the x and y points on that line where the intersection occurs, thus becoming the fixed point. 
                                x_fixed = (x + slope * (y - intercept)) / (slope**2 + 1) 
                                y_fixed = (slope*x + y*slope**2 + intercept) / (slope**2 + 1)
                                mistake_points.append([name, x, y, x_fixed, y_fixed, block_ref])
                                corrected_blocks.append([name, x_fixed, y_fixed, angle, name_error, block_ref])
                                mistake_exp.append([name, x, y, line_name, name_error, block_ref])
                        
                            found_match = True
                            break
            
            if not found_match: #No matches found at all within either tolerence return an error
                blocks_on_line.append([name, x, y, angle, None, None, 'Not On Line', 'Error'])
                mistake_points.append([name, x, y, None, None, block_ref])
                corrected_blocks.append([name, None, None, None, None, block_ref])
                mistake_exp.append([name, x, y, None, name_error, block_ref])

        (final_correct_blocks, final_corrected_blocks, 
         final_mistake_blocks, name_error_reason) = datafiltration.filter_name_errors(correct_blocks, corrected_blocks, mistake_points, mistake_exp, bedit_check)  

        all_blocks_correct_test = final_correct_blocks + final_corrected_blocks
        
        return blocks_on_line, final_mistake_blocks, final_corrected_blocks, all_blocks_correct_test, mistake_points, corrected_blocks, name_error_reason
     

    @staticmethod
    def filter_name_errors(correct_blocks, corrected_blocks, mistake_points, mistake_exp, bedit_check):
        """Function that filters through all blocks to see if there is a name error and returns it as a mistake""" 
        final_correct_blocks = []
        mistake_blocks_name = []
        name_error_reason = [] #list for explaing reasons due to a bedit 
        
        #Copying the already corrected blocks into the final list, then append any name erros to that list. 
        final_corrected_blocks = list(corrected_blocks)

        for block in correct_blocks:
            name, x, y, angle, name_error, block_ref = block

            if name_error is not None:
                final_corrected_blocks.append(block)
                mistake_blocks_name.append([name_error, x, y, angle, name_error, block_ref])
                if bedit_check != 1:
                    name_error_reason.append([name, x, y, None, True, False, block_ref])
            else:
                final_correct_blocks.append(block)

        # for block in correct_block_name_error: # IF there is no mistake on block position but its inside a bedit 
        #     name, x, y, name_error, line_name, block_ref = block 
        #     if name_error is not None and bedit_check != 1 : 
        #         name_error_reason.append([name, x, y, line_name, True, False, block_ref])

        for block in mistake_exp: 
            name, x, y, line_name, name_error, block_ref = block 
            if name_error is not None: 
                name_error_reason.append([name, x, y, line_name, True, True, block_ref])
            else: 
                name_error_reason.append([name, x, y, line_name, False, True, block_ref])            
            
        final_mistake_blocks = mistake_blocks_name + mistake_points

        return final_correct_blocks, final_corrected_blocks, final_mistake_blocks, name_error_reason
    
    @staticmethod 
    def find_line_error(filtered_lines, all_walls, line_properties, wall_slopes, wall_intercepts, tolerance1, tolerance2, tolerance3): 
        """This function goes through all the lines searching for errors. All lines should start and end at another line 
           Unless it is on the channel outline in which case the check just ensures hte line is on the channel outline  
           The code ensures that the end points of each line are on another line, there is a clause to prevent a line from checking itself against its own line
           If a mistake is identified in a line the closest slope and y intercept are returned (i.e the equation of the line that is closest to that line is returned)
           If a mistake is identified being too large the point will be returend as a mistake but no intercept or slope will be provided
           Thus mistake is flagged, no reasonable fix assumption for code to make"""

        line_mistakes = []
        correct_lines = []
        line_line_connections = []
        line_line_connections_check = []
        line_mistakes_check = []
        situation_where = []

        lines_OCO, lines_not_OCO, _= maths.Chanel_check_line(wall_slopes, wall_intercepts, filtered_lines, all_walls)

        correct_lines.extend(lines_OCO)

        for line in lines_not_OCO:  #Each start and end ponit of the line are checked against the slope and intercepts of the checker lines 
            name, x_start, y_start, x_end, y_end, offset, line_ref = line 

            line_key = (name, tuple(sorted([(x_start, y_start), (x_end, y_end)])))
         
            start_matches = False 
            end_matches = False 
            start_line_name = None 
            end_line_name = None 
            
            # Track closest lines for start and end points
            closest_start_slope = None
            closest_start_intercept = None
            min_start_dist = float('inf')
            temp_start_slope = None
            temp_start_intercept = None
            
            closest_end_slope = None
            closest_end_intercept = None
            min_end_dist = float('inf')
            temp_end_slope = None
            temp_end_intercept = None


            min_x = min(x for wall in all_walls for x, y in wall) #finding the boundaries of the shape 
            min_y = min(y for wall in all_walls for x,y in wall)
            max_x = max(x for wall in all_walls for x, y in wall)
            max_y = max(y for wall in all_walls for x, y in wall)
          

            if (x_start < (min_x - 0.2) or x_start > (max_x + 0.2) or y_start < (min_y- 0.2) or y_start > (max_y + 0.2) or
                x_end < (min_x - 0.2) or x_end > (max_x + 0.2) or y_end < (min_y - 0.2) or y_end > (max_y + 0.2)):
                start_matches = False 
                end_matches = False 
           

            for prop_line in line_properties: #These are the checker lines all lines (not on the channel outline) are checked 
                line_name, slope, intercept, x_s, y_s, x_e, y_e = prop_line

                line_checker_key = (name, tuple(sorted([(x_start, y_start), (x_end, y_end)])))
                
                same_line_forward = (abs(x_s - x_start) < 0.01 and abs(y_s - y_start) < 0.01 and #avoid checking a line against itself 
                                    abs(x_e - x_end) < 0.01 and abs(y_e - y_end) < 0.01)
                same_line_reverse = (abs(x_s - x_end) < 0.01 and abs(y_s - y_end) < 0.01 and 
                                    abs(x_e - x_start) < 0.01 and abs(y_e - y_start) < 0.01)
                
                tol = 1
                tol_match = 2

                avoid_same_formula_error_consx_x = (abs(x_s - x_start) < tol_match and abs(x_e - x_end) < tol_match
                                                    and abs(x_e - x_start) < tol_match and abs(x_s - x_end) < tol_match)
                avoid_same_formula_error_consx_y_start = ((y_s - tol) <= y_start <= (y_e + tol)) or ((y_e - tol) <= y_start <= (y_s + tol))                          
                avoid_same_formula_error_consx_y_end = ((y_s - tol) <= y_end <= (y_e + tol)) or ((y_e - tol) <= y_end <= (y_s + tol))  


                avoid_same_formula_error_consy_y = (abs(y_s - y_start) < tol_match and abs(y_e - y_end) < tol_match
                                                    and abs(y_e - y_start) < tol_match and abs(y_s - y_end) < tol_match )
                avoid_same_formula_error_consy_x_start = ((x_s - tol) <= x_start <= (x_e + tol)) or ((x_e - tol) <= x_start <= (x_s + tol)) 
                avoid_same_formula_error_consy_x_end = ((x_s - tol) <= x_end <= (x_e + tol)) or ((x_e - tol) <= x_end <= (x_s + tol))
                
                avoid_same_formula_error_consx_start = avoid_same_formula_error_consx_x and not avoid_same_formula_error_consx_y_start 
                avoid_same_formula_error_consx_end = avoid_same_formula_error_consx_x and not avoid_same_formula_error_consx_y_end
                
                avoid_same_formula_error_consy_start = avoid_same_formula_error_consy_y and not avoid_same_formula_error_consy_x_start 
                avoid_same_formula_error_consy_end = avoid_same_formula_error_consy_y and not avoid_same_formula_error_consy_x_end 
            
                tol_2 = 25
                #Lines are being checked against the equation of lines of other lines, an equation of a line assumes a lines length is infinite throuhgh space
                #the below code stops checking lines that are far from the line being checked to be corrected onto that line 
                avoid_distance_lines_x = ((x_s - tol_2) <= x_start <= (x_e + tol_2) or (x_e - tol_2) <= x_start <= (x_s + tol_2) or 
                                          (x_s - tol_2) <= x_end <= (x_e + tol_2)  or (x_e - tol_2) <= x_end <= (x_s + tol_2))
                

                avoid_distance_lines_y = ((y_s - tol_2) <= y_start <= (y_e + tol_2) or (y_e - tol_2) <= y_start <= (y_s + tol_2)
                                    or (y_s - tol_2) <= y_end <= (y_e + tol_2) or (y_e - tol_2) <= y_end <= (y_s + tol_2))
                
                # avoid_distance_lines_start = (x_s <= x_start <= x_e or x_e <= x_start <= x_s or y_s <= y_start <= y_e or y_e <= y_start <= y_s)
                # avoid_distance_lines_end = (x_s <= x_end <= x_e or x_e <= x_end <= x_s or y_s <= y_end <= y_e or y_e <= y_end <= y_s)
          
                min_distance = min(abs(x_start - x_s), abs(x_start - x_e),   #find miniumum distance to the line if not within the range
                    abs(x_end - x_s), abs(x_end - x_e),    
                    abs(y_start - y_s), abs(y_start - y_e), 
                    abs(y_end - y_s), abs(y_end - y_e))
                
                if (same_line_forward or same_line_reverse):
                    continue 
                if not avoid_distance_lines_x or not avoid_distance_lines_y:  #if the line is not within the range of the line then check if it is within a tolerence, than skip that line
                    continue 

                # Check start point and track closest - ONLY STORE TEMP VALUES
                if not start_matches:
                    if not (avoid_same_formula_error_consx_start or avoid_same_formula_error_consy_start): 
                        start_dist = maths.find_distance_to_line(x_start, y_start, slope, intercept)
                        if start_dist <= tolerance1: 

                            start_matches = True
                            start_line_name = line_name
                            x_s_checker_start = x_s
                            y_s_checker_start = y_s
                            x_e_checker_start = x_e
                            y_e_checker_start = y_e
                            
                        if start_dist < min_start_dist:
                            min_start_dist = start_dist
                            temp_start_slope = slope
                            temp_start_intercept = intercept
                            temp_start_name_conn = line_name 
                            x_s_start = x_s 
                            y_s_start = y_s
                            x_e_start = x_e
                            y_e_start = y_e


                # Check end point and track closest
                if not end_matches:     
                    if not (avoid_same_formula_error_consx_end or avoid_same_formula_error_consy_end): 
                        end_dist = maths.find_distance_to_line(x_end, y_end, slope, intercept) 
                    
                        if end_dist <= tolerance1: 
                            end_matches = True
                            end_line_name = line_name
                            x_s_checker_end = x_s
                            y_s_checker_end = y_s
                            x_e_checker_end = x_e
                            y_e_checker_end = y_e

                        if end_dist < min_end_dist:
                            min_end_dist = end_dist
                            temp_end_slope = slope
                            temp_end_intercept = intercept    
                            temp_end_name_conn = line_name   
                            x_s_end = x_s 
                            y_s_end = y_s
                            x_e_end = x_e
                            y_e_end = y_e

                if start_matches and end_matches: #If a match is found break 
                    break            

            #The below code takes the temp slopes and intercepts found in the above code, slopes and intercepts are split into different 
            if min_start_dist <= tolerance2:
                closest_start_slope = temp_start_slope
                closest_start_intercept = temp_start_intercept
                start_line_name = temp_start_name_conn
            elif tolerance2 < min_start_dist < tolerance3:
                closest_start_slope = None
                closest_start_intercept = None
                start_line_name = None 
            elif min_start_dist > tolerance3: #Distanc so big its probably not a mistake 
                start_matches = True    
                start_line_name = None 

            if min_end_dist <= tolerance2: 
                closest_end_slope = temp_end_slope
                closest_end_intercept = temp_end_intercept
                end_line_name = temp_end_name_conn
            elif tolerance2 < min_end_dist < tolerance3:
                closest_end_slope = None    
                closest_end_intercept = None
                end_line_name = None
            elif min_end_dist > tolerance3: 
                end_matches = True 
                end_line_name = None
            
            if not start_matches or not end_matches:  
                line_mistakes.append([name, x_start, y_start, x_end, y_end, 
                                      start_line_name, closest_start_slope, closest_start_intercept, 
                                      end_line_name, closest_end_slope, closest_end_intercept, line_ref])
                line_mistakes_check.append([name, x_start, y_start, x_end, y_end, start_line_name, end_line_name])
                line_line_connections_check.append([name, start_line_name, end_line_name, x_start, y_start, x_end, y_end, line_ref])
                # situation_where.append([name, x_start, y_start, x_end, y_end, start_line_name, end_line_name, x_s_end, y_s_end, x_e_end, y_e_end])

                #make sperate list for mistakes if name = name in function below than continue 
            if start_matches and end_matches: 
                correct_lines.append([name, x_start, y_start, x_end, y_end, offset, line_ref])
                line_mistakes_check.append([name, x_start, y_start, x_end, y_end, start_line_name, end_line_name])  
                line_line_connections.append([name, start_line_name, end_line_name, x_start, y_start, x_end, y_end, line_ref])  
                # situation_where.append([name, x_start, y_start, x_s_checker_start, y_s_checker_start, x_e_checker_start, y_e_checker_start,
                #                      x_end, y_end, x_s_checker_end, y_s_checker_end, x_e_checker_end, y_e_checker_end])  
          
        return line_mistakes, correct_lines, line_line_connections, line_line_connections_check
    
    
    @staticmethod
    def fix_line_mistakes(line_mistakes): 
        """This function fixes any errors recored in the find_line_error function, mathamtically vertical lines are account for in all scenarios 
           If both lines have slopes, functions are solved using simealtaneous equations 
           The function returns a list of fixed lines with their name, position, layer, and colour. """
        
        fixed_lines = []
        line_mistake_explain = []
        
        for line in line_mistakes: 
            (name, x_start, y_start, x_end, y_end, line_start_name, closest_start_slope,
              closest_start_intercept, line_end_name, closest_end_slope, closest_end_intercept, line_ref) = line 
     
            #Basically if line is too far away form anything leave it as it is (it is supposed to be like that)
            if (closest_start_slope is None and closest_start_intercept is None) or (closest_end_slope is None and closest_end_intercept is None): 
                new_x_start = x_start 
                new_y_start = y_start 
                new_x_end = x_end
                new_y_end = y_end

                fixed_lines.append([name, new_x_start, new_y_start, new_x_end, new_y_end, False, line_ref]) #Append these results so they are no longer checked
                continue

            elif x_start == x_end:  # Vertical line

                if closest_start_slope is None: #This is unlikely scenario, if both lines are vertical, probably that line is offset so it gets snapped onto the vertical line closest to it. 
                    x_intercept_start = float(closest_start_intercept.split()[2])
                    new_x_start = x_intercept_start 
                    new_y_start = y_start 
                else:
                    new_x_start = x_start  #if line has a slope 
                    new_y_start = closest_start_slope * x_start + closest_start_intercept #calculate where new y should be based on original line 
                
                if closest_end_slope is None: #same as above but for the end 
                    x_intercept_end = float(closest_end_intercept.split()[2])
                    new_x_end = x_intercept_end
                    new_y_end = y_end
                else:
                    new_x_end = x_end
                    new_y_end = closest_end_slope * x_end + closest_end_intercept
            
            else: #if slope of original line is not None 
                slope_line = (y_end - y_start) / (x_end - x_start) #original line has a slope value 
                intercept_line = y_start - slope_line * x_start  

                # FIX START POINT
                if closest_start_slope is None:
                    x_intercept_start = float(closest_start_intercept.split()[2])
                    new_x_start = x_intercept_start #new start point for the line will be x point on closest line 
                    new_y_start = slope_line * new_x_start + intercept_line  #plug new start x into formula to find new y point 
                        
                else: #both lines have slopes call sim eq func 
                    new_x_start, new_y_start = maths.solve_simultaneous_equations(closest_start_slope, closest_start_intercept, slope_line, intercept_line)
                    if new_x_start is None: 
                        new_x_start, new_y_start = x_start, y_start

                # Fix the end points, same logic as above. 
                if closest_end_slope is None:
                    x_intercept_end = float(closest_end_intercept.split()[2]) #move the line to the x point
                    new_x_end = x_intercept_end #move the line to the x point
                    new_y_end = slope_line * new_x_end + intercept_line #sub into equation to find new y point 
                        
                else: #Both lines have slopes call sim eq func 
                    new_x_end, new_y_end = maths.solve_simultaneous_equations(closest_end_slope, closest_end_intercept, slope_line, intercept_line)
                    if new_x_end is None: 
                        new_x_end, new_y_end = x_end, y_end

            fixed_lines.append([name, new_x_start, new_y_start, new_x_end, new_y_end, False, line_ref])
            line_mistake_explain.append([name, x_start, y_start, x_end, y_end, new_x_start,
                                         new_y_start, new_x_end, new_y_end, line_start_name, line_end_name, line_ref])

        return fixed_lines, line_mistake_explain
    
    @staticmethod
    def filter_offset_lines(correct_lines, line_mistakes): 
        """Function that filters offset lines in the case that all objects inside a module are inside a single block referernce"""
        bedit_lines = []

        bedit_lines = list(correct_lines) 

        for line in line_mistakes: 
            (name, x_start, y_start, x_end, y_end,_, _, _,_, _, _, line_ref) = line
            bedit_lines.append([name, x_start, y_start, x_end, y_end, False, line_ref])       

        return bedit_lines       



    
    @staticmethod
    def find_line_line_connections(fixed_lines, wall_slopes, wall_intercepts, all_walls, line_line_connections_check, line_line_connections):
        "finds lines that only connect between lines"

        """There is a rare scenario where there a line mistake and it is off the channel outline, when it should be
        For example: A 60 Header goes too far past a block. The code will initially think this line is off the channel outline. 
        We take the fixed points (suggested fix) and then see here if it is on the channel outline
        If it is on the channel outline it will be noticed here and it won't be added to the line line connections ensuring no error arises from database"""
        
        lines_OCO, _, _ = maths.Chanel_check_line(wall_slopes, wall_intercepts, fixed_lines, all_walls)
        
        ll_connections = []

        #Line line connections check are the mistake lines that needed to be checker to ennsure they don't lie on the channel outline 
        #the below code ensures any lines arnt mistakenly added to the line line connection type
        #lines on the channel outline should not be in this category they are in the line block type as they follow different rules
        for line_l in line_line_connections_check: 
                name, start_line_name, end_line_name, x_start_c, y_start_c, x_end_c, y_end_c, line_ref = line_l
                line_is_OCO = False 
                for line in lines_OCO: 
                    line_name, x_start, y_start, x_end, y_end, offset, line_ref = line
                    if line_name == name: 
                        if abs(x_start - x_start_c) < 25 and abs(y_start - y_start_c) < 25 and abs(x_end - x_end_c) < 25 and abs(y_end - y_end_c) < 25: 
                                line_is_OCO = True 

                if not line_is_OCO: 
                    ll_connections.append([name, start_line_name, end_line_name, x_start_c, y_start_c, x_end_c, y_end_c, line_ref])
            
        final_line_line_connections = line_line_connections + ll_connections 
        return final_line_line_connections    
    

    
    def link_line_block_connections(self, correct_lines, fixed_lines, blockrefs): 
        """ This function checks to see if lines start and end on block references """
        block_tolerences = self.block_tolerence(blockrefs)
        line_block_connections = [] 
        lines = correct_lines + fixed_lines
      
        for line in lines: 
            name, x_start, y_start, x_end, y_end, offset, line_ref = line 
            block_name_start = None 
            block_name_end = None  
         
            for block in block_tolerences: 
                block_name, x, y, x_tolerence, y_tolerence = block 

                if x is None or y is None: 
                    continue 

                tol = 1

                if x_tolerence is None and y_tolerence is None: 
                    if (abs(x_start - x) < 1 and abs(y_start - y) < 1):
                        block_name_start = block_name 
                    if abs(x_end - x) < 1 and abs(y_end - y) < 1: 
                        block_name_end = block_name #

                elif name == 'WALL':  #if walls start or end within the range of the block its on it
                    if (x - x_tolerence - tol) <= x_start <= (x + x_tolerence + tol) and (y - y_tolerence - tol) <= y_start <= (y_tolerence + y + tol):
                        block_name_start = block_name 
                    if (x - x_tolerence - tol) <= x_end <= (x + x_tolerence + tol) and (y - y_tolerence - tol) <= y_end <= (y_tolerence + y + tol):   
                        block_name_end = block_name 

                else: #Below are the scenarios of positions a line could be at, at the end of a block to be considered drawn to that block 
                    if ((abs(x_start - (x + x_tolerence)) < 1 and abs(y_start - y) < 1) or  
                        (abs(x_start - (x - x_tolerence)) < 1 and abs(y_start - y) < 1) or 
                        (abs(x_start - x) <1 and abs(y_start - (y + y_tolerence)) < 1) or 
                        (abs(x_start - x) < 1 and abs(y_start - (y - y_tolerence)) < 1) or
                        (abs(x_start - x) < 1 and abs(y_start - y) < 1 )
                        ): 
                        block_name_start = block_name 
                     
                    if  ((abs(x_end - (x + x_tolerence)) < 1 and abs(y_end - y) < 1) or 
                        (abs(x_end - (x - x_tolerence)) < 1 and abs(y_end - y) < 1) or 
                        (abs(x_end - x) < 1 and abs(y_end - (y + y_tolerence)) < 1) or 
                        (abs(x_end - x) < 1 and abs(y_end - (y - y_tolerence)) < 1) or 
                        (abs(x_end - x) < 1 and abs(y_end - y) < 1) 
                        ): 
                        block_name_end = block_name 
                    
               
            line_block_connections.append([name, block_name_start, block_name_end, x_start, y_start, x_end, y_end, line_ref]) 
        lines_on_blocks = self.filter_line_block_connections(line_block_connections) 

        return lines_on_blocks
    
    def filter_line_block_connections(self, line_block_connections): 
        filtered_line_conn = []
        for line in line_block_connections:
            name, block_name_start, block_name_end, x_start, y_start, x_end, y_end, line_ref = line 
            if (block_name_start is None or block_name_start == 'TRUSS VERTICAL') and (block_name_end is None or block_name_end == 'TRUSS VERTICAL'): 
                continue 
            filtered_line_conn.append([name, block_name_start, block_name_end, x_start, y_start, x_end, y_end, line_ref])
        return filtered_line_conn
 
    def block_tolerence(self, blockrefs): 
        """ The width and height of CPSHS blocks are defined in their name. This function extracts the width and height values to allow for lines to be drawn 
        to just the edge of blocks"""

        block_tolerences = [] 
        for block in blockrefs: 
            name, x, y, angle, name_error, block_ref = block
            x_tolerence = None 
            y_tolerence = None 
    
            if name.upper().startswith("CPSHS"):
                
                remaining = name[5:]  # remove "CPSHS"
                
                remaining = remaining.split("-")[0]  # Remove anything after "-" (like -B)

                parts = remaining.lower().split("x") # Split on x or X
                
                x_tolerence = int(parts[0])
                y_tolerence = int(parts[1])

            if name.upper().startswith("NLB"): 
                parts = name.split()        # ['NLB', '30', 'CENTRE']
                value = int(parts[1]) / 2   # 15 (half-width for tolerance)
                x_tolerence = value
                y_tolerence = value

            block_tolerences.append([name, x, y, x_tolerence, y_tolerence])
        return block_tolerences   

    

    





                
            


                

