import math


class Mathematical:
    """This class does the backend maths calculations for the interface and updated dxf 
       This class contains six functison 
       wall_len: This calculates the length of walls 
       slope_vales: Function goes through different line situatiosn returning slope, intercept, start and end values fore each line and wall. 
       calc_slope: returns actual slope and intercept value so calculation does not need to be repeated for different scenarios 
       Shape_outline: Filters through all blocks and lines to ensure only data being picked up is wanted. 
       find_distance_to_line: Subs points into equation of a line 
       solve_simultaneous_equations: solves simealtaneous equations for where a point should be position on a line """

    @staticmethod
    def wall_len(all_lines):
        wall_lengths = []
        for line in all_lines:
            name, x_start, y_start, x_end, y_end, offset, line_ref = line
            delta_x = x_start - x_end
            delta_y = y_start - y_end
            distance = math.sqrt((delta_x)**2 + (delta_y)**2)
            wall_lengths.append(distance)
        return wall_lengths
    
    @staticmethod
    def slope_values(all_lines, all_walls):
        #takes all lines and all_walls from autocad 
        #This function creates the equation of the line for each line (Channel outline and interior lines)
        #Functions accounts for vertical lines

        slopes = [] 
        y_intercepts = []
        line_properties = []
        wall_slopes = []
        wall_intercepts = []

        for line in all_lines: 
            line_name, x_start, y_start, x_end, y_end, mistake, line_ref = line  
            line_slopes, line_intercepts = Mathematical.calc_slope(x_start, y_start, x_end, y_end)
            slopes.append(line_slopes)
            y_intercepts.append(line_intercepts)
            line_properties.append([line_name, line_slopes, line_intercepts, x_start, y_start, x_end, y_end])
                    
        # for walls in all_walls:  
        for i in range(len(all_walls)):  
            p1 = all_walls[i]
            p2 = all_walls[(i+1) % len(all_walls)]

            slope_wall, intercept_wall = Mathematical.calc_slope(p1[0], p1[1], p2[0], p2[1])
            wall_slopes.append(slope_wall)
            wall_intercepts.append(intercept_wall)  
            line_properties.append(['CHANNEL OUTLINE', slope_wall, intercept_wall, p1[0], p1[1], p2[0], p2[1]])  

        return slopes, y_intercepts, line_properties, wall_slopes, wall_intercepts

    @staticmethod
    def calc_slope(x1, y1, x2, y2):
        if abs(x2 - x1) < 0.3:
            slope = None
            c = f'X Intercept {x1}'
        else:
            slope = (y2 - y1) / (x2 - x1)
            c = y1 - (slope * x1)
        return slope, c
    

    @staticmethod
    def blockcheck(block_names, x_min, x_max, y_min, y_max):
        block_checks = []
        for block in block_names:
            name, x, y = block
            if x_min <= x <= x_max and y_min <= y <= y_max:
                block_checks.append([name, x, y])

        return block_checks


    @staticmethod
    def Shape_outline(Blockref_Points, all_walls, x_min, x_max, y_min, y_max):
        #This function Filters the Block References and Points to ensure any unwanted Points are not picked up
        filtered_blockref = []

        for block in Blockref_Points:
            name, x, y, angle, name_error, block_ref = block

            if x_min <= x <= x_max and y_min <= y <= y_max:
                filtered_blockref.append([name, x, y, angle, name_error, block_ref])

        all_x = []
        all_y = []

        for _, x, y, _, _, _ in filtered_blockref:
            all_x.append(x)
            all_y.append(y)

        filtered_walls = []
        for wall in all_walls:
            for point in wall:
                x, y = point[0], point[1]
                if x_min <= x <= x_max and y_min <= y <= y_max:
                    all_x.append(x)
                    all_y.append(y)
                    filtered_walls.append([x, y])


        return filtered_blockref, filtered_walls
    

    @staticmethod
    def filter_lines(lines, x_min, x_max, y_min, y_max): 
        filtered_lines = []
        for line in lines: 
            name, x_start, y_start, x_end, y_end, offset, line_ref = line   
            if x_min <= x_start <= x_max and x_min <= x_end <= x_max and y_min <= y_start <= y_max and y_min <= y_end <= y_max: 
                filtered_lines.append([name, x_start, y_start, x_end, y_end, offset, line_ref]) 

        return filtered_lines         

    
    @staticmethod
    def find_distance_to_line(x_point, y_point, slope, intercept):
        if slope is None:
            x_intercept = float(intercept.split()[2])
            return abs(x_point - x_intercept)

        else:
            return abs(y_point - (slope * x_point + intercept))

    @staticmethod
    def solve_simultaneous_equations(closest_slope, closest_intercept, slope_line, intercept_line):
        # y = m1*x + c1 and y = m2*x + c2  →  x = (c2-c1)/(m1-m2)
        denom = closest_slope - slope_line
        if abs(denom) < 1e-10:
            return None, None
        x_sol = (slope_line - closest_slope) / (closest_slope - slope_line)
        x_sol = (intercept_line - closest_intercept) / denom
        y_sol = closest_slope * x_sol + closest_intercept
        return float(x_sol), float(y_sol)
    
    @staticmethod
    def Channel_check_block(wall_slopes, wall_intercepts, blockrefs, block_tol): 
        blocks = []

        for block in blockrefs: 
            block_name, x, y, angle, _, block_ref = block 
            on_channel = 'No'

            for i in range(len(wall_slopes)): 
                wall_slope = wall_slopes[i]
                wall_intercept = wall_intercepts[i]

                if wall_slope is None: 
                    x_intercept = float(wall_intercept.split()[2])
                    x_d = abs(x_intercept - x)
                    if x_d < block_tol: 
                        on_channel = 'Yes'
                        break       
                else: 
                    y_d = abs(y - (wall_slope * x + wall_intercept))
                    if y_d < block_tol: 
                        on_channel = 'Yes'
                        break 

            blocks.append([block_name, x, y, angle, on_channel, block_ref])
        return blocks

    @staticmethod
    def Chanel_check_line(wall_slopes, wall_intercepts, lines, all_walls): 

        lines_OCO = []
        lines_not_OCO = []
        lines_cl = []

        for line in lines: 
            name, x_start, y_start, x_end, y_end, offset, line_ref = line

            min_x = min(x for wall in all_walls for x, y in wall) #finding the boundaries of the shape 
            min_y = min(y for wall in all_walls for x,y in wall)
            max_x = max(x for wall in all_walls for x, y in wall)
            max_y = max(y for wall in all_walls for x, y in wall)

            # Check boundaries ONCE (no loop needed)
            if (x_start < (min_x - 1) or x_start > (max_x + 1) or y_start < (min_y- 1) or y_start > (max_y + 1) or
                x_end < (min_x - 1) or x_end > (max_x + 1) or y_end < (min_y - 1) or y_end > (max_y + 1)):
                lines_not_OCO.append([name, x_start, y_start, x_end, y_end, offset, line_ref])
                lines_cl.append([name, x_start, y_start, x_end, y_end, 'No', line_ref])
                continue
            on_channel_outline = False 

            for i in range(len(wall_slopes)): 
                wall_slope = wall_slopes[i]
                wall_intercept = wall_intercepts[i]
                
                # Main check for a point on the channel outline
                if wall_slope is None:  # Vertical wall
                    x_intercept = float(wall_intercept.split()[2]) 
                    x_sd = abs(x_intercept - x_start)
                    x_ed = abs(x_intercept - x_end)
                    if x_ed < 1 and x_sd < 1:
                        on_channel_outline = True 
                        break
                      
                else:  # Wall with slope
                    y_ss = abs(y_start - (wall_slope * x_start + wall_intercept))
                    y_ee = abs(y_end - (wall_slope * x_end + wall_intercept))
                    if y_ss < 1 and y_ee < 1: 
                        on_channel_outline = True 
                        break

            if on_channel_outline:
                lines_OCO.append([name, x_start, y_start, x_end, y_end, offset, line_ref])
                lines_cl.append([name, x_start, y_start, x_end, y_end, 'Yes', line_ref])
            else:
                lines_not_OCO.append([name, x_start, y_start, x_end, y_end, offset, line_ref])
                lines_cl.append([name, x_start, y_start, x_end, y_end, 'No', line_ref])

        return lines_OCO, lines_not_OCO, lines_cl              
            
    @staticmethod
    def return_error(final_corrected_blocks, mistake_points):
        """ This function ensures that blocks that have not been fixed are returned as an error
        this situation arises when blocks are too far away from anything they are not fixed """

        finals_corrected_blocks = []

        for block in final_corrected_blocks: 
            name, x, y, angle, name_error, block_ref = block 

            if len(mistake_points) == 0:
                finals_corrected_blocks.append([name, x, y, angle, name_error, block_ref])
                continue

            matched = False
            for mistake_block in mistake_points: 
                name_m, x_m, y_m, angle_m, name_error_m, block_ref_m = mistake_block

                if name_m == name: 
                    matched = True
                    if abs(x_m - x) < 0.01 and abs(y_m - y) < 0.01: 
                        finals_corrected_blocks.append([name, None, None, None, None])
                    else: 
                        finals_corrected_blocks.append([name, x, y, angle, name_error, block_ref])
                    break 

            if not matched:
                finals_corrected_blocks.append([name, x, y, angle, name_error, block_ref])

        return finals_corrected_blocks               

            