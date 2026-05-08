
from ezdxf.lldxf import const
import math
from itertools import combinations

class file_presentation: 
    """This class is for dealing with any changes made to the autocad file itself to portray any errors and why they have occured 

    explain_mistakes_dxf: The main function goes through all hte possible mistake lines, unpacks their points and calls the necessary functions 
    to correctly display any errors 

    link_shape_line: This function links the mistake line or block with the shape that is flagging it, in autocad lines may be under other lines therefore
    when the user selects on the error line shape the line is also highlighted making it clear what line an error has occured on 

    draw_group_hyperlink: This function extracts the mistake explanation and adds it to the joint object and shape flagging the error, this makes it 
    clear to the user why a mistake is occuring 

    create_separation: If a few mistakes converge on a single point (due to lines ending at the same point or lines being on top of eachtoher) there may 
    be mulitple errors being flagged but only one would be clear to the user, this function chekcs if more than one mistake flagger shape is located at 
    a single point, if so it will slightly offset both shapes allowing for all error flags to be clearly visible to the user 

    draw_triangle: Function that just draws a triangle on a mistake point (mistake flagger)
    
    """

    def explain_mistakes_dxf(self, msp, duplicate_lines, mistake_block_reason, mistake_line_reasons, post_rejected_block, post_rejected_line, all_fail, doc, bedit_line_map, bedit_block_map):

        sep_duplicate_lines = self.create_separation(duplicate_lines, 'Duplicate')
        for i, line in enumerate(sep_duplicate_lines):  # flagging a duplicate line
            name, x_s, y_s, x_e, y_e, line_ref, reason = line
            triangle1 = self.draw_triangle(msp, x_s, y_s)
            triangle2 = self.draw_triangle(msp, x_e, y_e)
            resolved_line_ref = bedit_line_map.get(line_ref, line_ref)
            self.link_shape_line(resolved_line_ref, triangle1, triangle2, name, 'Duplicate', i, doc)
            self.draw_group_hyperlink(resolved_line_ref, reason, triangle1, triangle2, i)

        for i, block in enumerate(mistake_block_reason):
            name_b, x_b, y_b, reason, block_ref = block
            circle = msp.add_circle(center=(x_b, y_b), radius=75, dxfattribs={"color": 1})
            circle.set_xdata('PE_URL', [
                (1000, ""),
                (1002, "{"),
                (1000, reason),
                (1000, ""),
                (1002, "}"),
            ])
            resolved_block_ref = bedit_block_map.get(block_ref, block_ref)
            self.link_shape_line(resolved_block_ref, circle, None, name_b, 'Block', i, doc)
            self.draw_group_hyperlink(resolved_block_ref, reason, circle, None, i)
            
        for i, mistake_line in enumerate(mistake_line_reasons):
            name_l, x_l, y_l, line_ref, reason = mistake_line
            circle = msp.add_circle(center=(x_l, y_l), radius=75, dxfattribs={"color": 1})
            resolved_line_ref = bedit_line_map.get(line_ref, line_ref)
            self.link_shape_line(resolved_line_ref, circle, None, name_l, 'Geometry', i, doc)
            self.draw_group_hyperlink(resolved_line_ref, reason, circle, None, i)

        for i, block in enumerate(post_rejected_block):  #explaing why a rejected block from object database was rejected
            name, x, y, reason, block_ref = block 
            triangle = self.draw_triangle(msp, x, y)
            triangle.set_xdata('PE_URL', [(1000, ""),(1002, "{"),(1000, reason),(1000, ""),(1002, "}"),])
            resolved_block_ref = bedit_block_map.get(block_ref, block_ref)
            self.link_shape_line(resolved_block_ref, triangle, None, name, 'Object_DB_Block', i, doc)
            self.draw_group_hyperlink(resolved_block_ref, reason, triangle, None, i)

        seperation_lines = self.create_separation(all_fail, 'Category_db') #ensuring there is no overlap between triangles 0
        for i, seperation_line in enumerate(seperation_lines):
            line_name, x_start, y_start, line_start_category, x_end, y_end, line_end_category, reason, line_ref = seperation_line
            triangle1 = self.draw_triangle(msp, x_start, y_start)
            triangle2 = self.draw_triangle(msp, x_end, y_end)
            resolved_line_ref = bedit_line_map.get(line_ref, line_ref)
            self.link_shape_line(resolved_line_ref, triangle1, triangle2, line_name, 'Category', i, doc)  
            self.draw_group_hyperlink(resolved_line_ref, reason, triangle1, triangle2, i)

        sep_object_lines = self.create_separation(post_rejected_line, 'Object_db')
        for i, line in enumerate(sep_object_lines):   #why a rejected line from object database was rejected
            name, x_s, y_s, x_e, y_e, reason, line_ref = line     
            triangle1 = self.draw_triangle(msp, x_s, y_s)
            triangle2 = self.draw_triangle(msp, x_e, y_e)
            resolved_line_ref = bedit_line_map.get(line_ref, line_ref)
            self.link_shape_line(resolved_line_ref, triangle1, triangle2, name, 'Object', i, doc)
            self.draw_group_hyperlink(resolved_line_ref, reason, triangle1, triangle2, i)

    
    def link_shape_line(self, ref, shape1, shape2, name, error_type, i, doc): 
        group_name = f'{error_type}_ERROR_{name}_{i}'
        if doc.groups.get(group_name) is not None:
                doc.groups.delete(group_name)
        group = doc.groups.new(group_name)
        if shape2 is None: 
            members = [e for e in [shape1, ref] if e is not None]
        else:
            members = [e for e in [shape1, shape2, ref] if e is not None] 
        try:
            group.extend(members)
        except const.DXFStructureError:
            shapes_only = [e for e in [shape1, shape2] if e is not None]
            if shapes_only:
                group.extend(shapes_only)
                

    def draw_group_hyperlink(self, ref, reason, shape1, shape2, i): 
        """Function for attaching a hyperlink to an error 
        the function attaches the hyperlink to the line and the shapes that flag the error"""
        xdata = [(1000, ""),(1002, "{"),(1000, reason),(1000, ""),(1002, "}"),]
        if shape1 is not None:
            shape1.set_xdata('PE_URL', xdata)
        if shape2 is not None:
            shape2.set_xdata('PE_URL', xdata)

        ref.set_xdata('PE_URL', [(1000, ""),(1002, "{"),(1000, reason),(1000, ""),(1002, "}"),])

                
    def create_separation(self, lines, type):
        if type in ('Duplicate', 'Object_db'):
            x_end_idx = 3
        else:  # Category_db
            x_end_idx = 4

        for i, j in combinations(range(len(lines)), 2):
            line1 = list(lines[i])
            line2 = list(lines[j])

            if type == 'Duplicate' or type == 'Object_db':
                line_name1, x_start1, y_start1, x_end1, y_end1, line_ref1, reason1 = line1
                line_name2, x_start2, y_start2, x_end2, y_end2, line_ref2, reason2 = line2

            if type == 'Category_db':
                line_name1, x_start1, y_start1, line_start_category1, x_end1, y_end1, line_end_category1, reason1, line_ref1 = line1
                line_name2, x_start2, y_start2, line_start_category2, x_end2, y_end2, line_end_category2, reason2, line_ref2 = line2

            if x_start1 is not None and x_start2 is not None and y_start1 is not None and y_start2 is not None:
                if abs(x_start1 - x_start2) < 1 and abs(y_start1 - y_start2) < 1:
                    line1[1] += 10
                    line2[1] -= 10

            if x_end1 is not None and x_end2 is not None and y_end1 is not None and y_end2 is not None:
                if abs(x_end1 - x_end2) < 1 and abs(y_end1 - y_end2) < 1:
                    line1[x_end_idx] += 10
                    line2[x_end_idx] -= 10

            if x_start1 is not None and x_end2 is not None and y_start1 is not None and y_end2 is not None:
                if abs(x_start1 - x_end2) < 1 and abs(y_start1 - y_end2) < 1:
                    line1[1] += 10
                    line2[x_end_idx] -= 10

            if x_start2 is not None and x_end1 is not None and y_start2 is not None and y_end1 is not None:
                if abs(x_start2 - x_end1) < 1 and abs(y_start2 - y_end1) < 1:
                    line2[1] += 10
                    line1[x_end_idx] -= 10

            lines[i] = tuple(line1)
            lines[j] = tuple(line2)

        return lines                     

    def draw_triangle(self, msp, x, y): 
        """Draws triangle around end points of where duplicate line occured"""
        if x is None or y is None: 
            return None 
        displacement = 120
        point1 = x, y + displacement #90 degrees 
        point2 = x + displacement * math.cos(-0.523599), y + displacement * math.sin(-0.523599) # -30 degrees 
        point3 = x + displacement * math.cos(3.66519), y + displacement * math.sin(3.66519)   # -150 degrees 
        points = [point1, point2, point3]
        triangle = msp.add_lwpolyline(points, close=True, dxfattribs={'layer': 'CORRECTION_HIGHLIGHT', 'color': 1})

        return triangle 

        
