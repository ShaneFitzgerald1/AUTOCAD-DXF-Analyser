
class presentation: 
    """This class establishes lists to allow for neat presenation of results inside GUI
       This class contains two functions 
       combine_slope_walls: combines wall slopes lengths and intercepts into a singular list so can be passed through base_table.py and table_widget.py 
       what_line: Filters if poins are on the channel outline for presentation in GUI table. """

    @staticmethod
    def combine_slope_walls(wall_lengths, slopes, y_intercepts): 
        #This function uses the zip function to combine lists so they can be put into the populate table function easily
        wall_slope_intercept = [[length, slope, intercept] for length, slope, intercept 
                            in zip(wall_lengths, slopes, y_intercepts)]  
        return wall_slope_intercept
    
    @staticmethod
    def what_line(blocks_on_line, filtered_walls, all_lines, tolerance):
    #This is an extra function it checks each Block Referne and Line to see if they lie on the channel outline 
    # Results are appended for table just to show in the interface 
        on_line_points = []
        all_lines_table = []

        wall_x_coords = [point[0] for point in filtered_walls]
        wall_y_coords = [point[1] for point in filtered_walls]

        for block in blocks_on_line:
            name, x, y, angle, wall, wall_type, on_line, mistake = block 

            if any(abs(x - wall_x) <= tolerance for wall_x in wall_x_coords) or any(abs(y-wall_y) <= tolerance for wall_y in wall_y_coords): 
                on_line_points.append([name, x, y, angle, wall, wall_type, on_line, mistake, 'Yes'])
            else: 
                on_line_points.append([name, x, y, angle, wall, wall_type, on_line, mistake, 'No'])

        for line in all_lines:
            name, x_start, y_start, x_end, y_end, offset, line_ref = line

            if any(abs(x_start - wall_x) <= tolerance for wall_x in wall_x_coords):  # Check if line is on a vertical wall (x_start == x_end and that x is a wall x)
                    all_lines_table.append([name, x_start, y_start, x_end, y_end, 'Yes'])
            elif any(abs(y_start - wall_y) <= tolerance for wall_y in wall_y_coords):
                all_lines_table.append([name, x_start, y_start, x_end, y_end, 'Yes'])
            else: 
                all_lines_table.append([name, x_start, y_start, x_end, y_end, 'No'])  

        return on_line_points, all_lines_table
    
    @staticmethod
    def dxf_mistake_explained(wall_points, mistake_exp): 

        mistake_block_reason = []

        for block in mistake_exp:
            name, x, y, line_name, xs, ys, xe, ye = block 
            if abs(x - xs) <= 5 and abs(y-ys) <= 5: #figuring out what point is connected to what end of line 
                mistake_block_reason.append([name, x, y, f'{name} is not on {line_name}'])



            

