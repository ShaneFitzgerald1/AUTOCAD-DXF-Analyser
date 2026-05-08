import math 
from collections import defaultdict
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
       flag_duplicate_lines: removes any duplicates and ensures there are no repeats of identical lines 
       On_Channel_Outline: Corrects block references that are not located on any lines
       filter_name_errors: flags blocks that have a name error as a mistake
       find_line_error: Locates any line errors 
       fix_line_error: Fixes any line errors 
        """
    
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
    def find_fix_block_errors(filtered_blockref, filtered_walls, line_properties, bedit_check, tolerance1, tolerance2):
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
                    avoid_distant_lines = (xs - tolerance1 <= x <= xe + tolerance1 or xe - tolerance1 <= x <= xs + tolerance1
                                            or ys - tolerance1 <= y <= ye + tolerance1 or ye - tolerance1 <= y <= y + tolerance1)
                                
                    min_distance = min(abs(x - xs), abs(x - xe),   #find miniumum distance to the line if not within the range    
                        abs(y - ys), abs(y - ye))
                    
                    if not avoid_distant_lines and (min_distance > tolerance2):  #if the block is not within the range of the line then check if it is within a tolerence, than skip that line
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
        line_mistakes_check = []

        lines_OCO, lines_not_OCO, _= maths.Chanel_check_line(wall_slopes, wall_intercepts, filtered_lines, all_walls)

        correct_lines.extend(lines_OCO)
  
        for line in lines_not_OCO:  #Each start and end ponit of the line are checked against the slope and intercepts of the checker lines 
            name, x_start, y_start, x_end, y_end, offset, line_ref = line 

            line_key = (name, tuple(sorted([(x_start, y_start), (x_end, y_end)])))
         
            #set the flag values 
            start_matches = False 
            end_matches = False 

            min_start_dist = float('inf')
            temp_start_slope = None
            temp_start_intercept = None
            min_end_dist = float('inf')
            temp_end_slope = None
            temp_end_intercept = None

            #find the slope of each line to compare to that of hte checker lines 
            line_slope, line_intercept = maths.calc_slope(x_start, y_start, x_end, y_end)

            for prop_line in line_properties:  #line properties are the checker lines 
                line_name, slope, intercept, x_s, y_s, x_e, y_e = prop_line

                line_checker_key = (line_name, tuple(sorted([(x_s, y_s), (x_e, y_e)]))) #ensuring line isnt checked against itself 
                if line_key == line_checker_key:
                    continue

                skip_start_line = False 
                skip_end_line = False 
                run_check = False 
                #This part of the code ensures that colinear lines dont correct lines despite being far away, 
                #If the slope and intercept of a line are the same, the code ensures they are near enough to eachtoher to be considered fixable by that lien 
                # Its necessary to check the x and y for both start and end poitns giving four different situations. 
                if slope is None and line_slope is None: 
                    intercept_1 = float(intercept.split()[2])
                    line_intercept_1 = float(line_intercept.split()[2])
                    if abs(line_intercept_1 - intercept_1) < 0.1: 
                        run_check = True 
                if (slope == line_slope and intercept == line_intercept):
                    run_check = True 
                if run_check: 
                    skip_start_line = datafiltration.skip_line_on_path(x_start, y_start, x_s, x_e, y_s, y_e, tolerance1)

                    skip_end_line = datafiltration.skip_line_on_path(x_end, y_end, x_s, x_e, y_s, y_e, tolerance1)
            
                tol_2 = 25
                #Lines are being checked against the equation of lines of other lines, an equation of a line assumes a lines length is infinite throuhgh space
                #the below code stops checking lines that are far from the line being checked to be corrected onto that line 
                avoid_distance_lines_x = ((x_s - tol_2) <= x_start <= (x_e + tol_2) or (x_e - tol_2) <= x_start <= (x_s + tol_2) or 
                                          (x_s - tol_2) <= x_end <= (x_e + tol_2)  or (x_e - tol_2) <= x_end <= (x_s + tol_2))
                avoid_distance_lines_y = ((y_s - tol_2) <= y_start <= (y_e + tol_2) or (y_e - tol_2) <= y_start <= (y_s + tol_2)
                                    or (y_s - tol_2) <= y_end <= (y_e + tol_2) or (y_e - tol_2) <= y_end <= (y_s + tol_2))
                
                if not avoid_distance_lines_x or not avoid_distance_lines_y:  #if the line is not within the range of the line then check if it is within a tolerence, than skip that line
                    continue 

                # Check start point and track closest - ONLY STORE TEMP VALUES
                if not start_matches and not skip_start_line:
                        start_dist = maths.find_distance_to_line(x_start, y_start, slope, intercept)
                        if start_dist <= tolerance1: 
                            start_matches = True
                            start_line_name = line_name
                        if start_dist < min_start_dist:
                            min_start_dist = start_dist
                            temp_start_slope = slope
                            temp_start_intercept = intercept
                            temp_start_name_conn = line_name 

                # Check end point and track closest
                if not end_matches and not skip_end_line:     
                        end_dist = maths.find_distance_to_line(x_end, y_end, slope, intercept) 
                        if end_dist <= tolerance1: 
                            end_matches = True
                            end_line_name = line_name
                        if end_dist < min_end_dist:
                            min_end_dist = end_dist
                            temp_end_slope = slope
                            temp_end_intercept = intercept    
                            temp_end_name_conn = line_name   

                if start_matches and end_matches: #If a match is found break 
                    break            

            #The below code takes the temp slopes and intercepts found in the above code, slopes and intercepts are split into different 

            start_matches, closest_start_slope, closest_start_intercept, start_line_name = datafiltration.sort_line_values(
            min_start_dist, tolerance1, tolerance2, tolerance3, temp_start_slope, temp_start_intercept, temp_start_name_conn, start_matches)

            end_matches, closest_end_slope, closest_end_intercept, end_line_name = datafiltration.sort_line_values(
            min_end_dist, tolerance1, tolerance2, tolerance3, temp_end_slope, temp_end_intercept, temp_end_name_conn, end_matches)
            
            if not start_matches or not end_matches:  
                line_mistakes.append([name, x_start, y_start, x_end, y_end, 
                                      start_line_name, closest_start_slope, closest_start_intercept, 
                                      end_line_name, closest_end_slope, closest_end_intercept, line_ref])
                line_mistakes_check.append([name, x_start, y_start, x_end, y_end, start_line_name, end_line_name])
                line_line_connections.append([name, start_line_name, end_line_name, x_start, y_start, x_end, y_end, line_ref])

                #make sperate list for mistakes if name = name in function below than continue 
            if start_matches and end_matches: 
                correct_lines.append([name, x_start, y_start, x_end, y_end, offset, line_ref])
                line_mistakes_check.append([name, x_start, y_start, x_end, y_end, start_line_name, end_line_name])  
                line_line_connections.append([name, start_line_name, end_line_name, x_start, y_start, x_end, y_end, line_ref])  
        
        return line_mistakes, correct_lines, line_line_connections
    
    @staticmethod
    def sort_line_values(min_distance, tolerance1, tolerance2, tolerance3, temp_slope, temp_intercept, temp_name_conn, matches): 
        """Im going ot move this function will keep it here until i figure out where to put it
        function that sorts the output slope intercepts and line names of the corrector lines """
        closest_slope = None 
        closest_intercept = None 
        line_name = None 

        if min_distance <= tolerance2:
                closest_slope = temp_slope
                closest_intercept = temp_intercept
                line_name = temp_name_conn
        elif min_distance > tolerance3: #Distance so big its probably not a mistake 
            matches = True 

        return matches, closest_slope, closest_intercept, line_name    

    def skip_line_on_path(x, y, x_start_check, x_end_check, y_start_check, y_end_check, tolerance1):  
        skip_line = False 

        start_x_in_range = (x_start_check - tolerance1 <= x <= x_end_check + tolerance1 or 
                                x_end_check - tolerance1 <= x_start_check <= x_start_check + tolerance1)
        start_y_in_range = (y_start_check - tolerance1 <= y <= y_end_check + tolerance1 or 
                    y_end_check - tolerance1 <= y <= y_start_check + tolerance1)
        if not start_x_in_range or not start_y_in_range: 
            skip_line = True 

        return skip_line    
            

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


