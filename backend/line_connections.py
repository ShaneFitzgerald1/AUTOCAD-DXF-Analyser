import math 
from collections import defaultdict
from backend.mathematical import Mathematical


class line_connections: 
    """This class sorts the lines by what connections they have 
    line_line_block_connections: Main function that returns lines that start and end on blocks, combines everything
    This function changes all the fixed block points back to the error points 

    iterate_line_block_connections: This function checks to see if line start and end poins lie on blocks 

    filter_line_block_connections: this function removes any lines that don't lie on a block from the lines on block list 

    sort_line_block_line_conns: the function ensures that lines from line line connections that should be on blocks are removed from that list

    block_tolerences: if lines start and end on the outskirts of a shape this is acceptable, this function sees where a shape starts and ends based on its name
    """
    def link_line_block_connections(self, correct_lines, fixed_lines, line_mistakes, blockrefs): 
        """ This function checks to see if lines start and end on block references """

        correct_lines_on_blocks = self.iterate_line_block_connections(correct_lines, blockrefs)
        fixed_lines_on_blocks = self.iterate_line_block_connections(fixed_lines, blockrefs)

        mistakes_by_ref = {m[-1]: m for m in line_mistakes}

        for i in range(len(fixed_lines_on_blocks)):
            name, block_name_start, block_name_end, _, _, _, _, line_ref = fixed_lines_on_blocks[i]
            if line_ref in mistakes_by_ref:
                _, m_x_start, m_y_start, m_x_end, m_y_end, *_ = mistakes_by_ref[line_ref]
                fixed_lines_on_blocks[i] = [name, block_name_start, block_name_end, m_x_start, m_y_start, m_x_end, m_y_end, line_ref]

        blocks_on_line = correct_lines_on_blocks + fixed_lines_on_blocks

        return blocks_on_line

    

    def iterate_line_block_connections(self, lines, blockrefs): 
        """This function is for looking through line types to see if the correct and correct lines are on blocks
        I could pass the inital incorrect line points through this but mistakes will always get flagged initially by the geometry engine
        I believe that it would jsut make things overwhelming and unclear for hte user if there were loads of mistakes being flagged at one single point"""
        block_tolerences = self.block_tolerence(blockrefs)
        line_block_connections = [] 


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
        lines_on_block = []

        for line in line_block_connections:
            name, block_name_start, block_name_end, x_start, y_start, x_end, y_end, line_ref = line 
            if not ((block_name_start is None or block_name_start == 'TRUSS VERTICAL') and \
            (block_name_end is None or block_name_end == 'TRUSS VERTICAL') and \
            not (block_name_start == 'TRUSS VERTICAL' and block_name_end == 'TRUSS VERTICAL')):
                lines_on_block.append([name, block_name_start, block_name_end, x_start, y_start, x_end, y_end, line_ref])

        return lines_on_block


    def sort_line_block_line_conns(self, lines_on_block, final_line_line_connections): 
        """This function filters the line_line_connections and the lines_on_block
        Function makes sure no liens are in both lists"""
        l_l_connections = []
        for line in final_line_line_connections: 
            already_exists = False 
            name, start_line_name, end_line_name, x_start_c, y_start_c, x_end_c, y_end_c, line_ref = line 
            for line_not_on_block in lines_on_block:
                name_ob, _, _, x_start, y_start, x_end, y_end, _ = line_not_on_block 
                if name_ob == name: 
                    if x_start_c == x_start and y_start_c == y_start and x_end_c == x_end and y_end_c == y_end: 
                        already_exists = True 
            
            if not already_exists: 
                l_l_connections.append([name, start_line_name, end_line_name, x_start_c, y_start_c, x_end_c, y_end_c, line_ref])

        return l_l_connections     

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

