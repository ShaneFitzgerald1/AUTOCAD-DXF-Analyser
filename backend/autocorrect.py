import ezdxf
from ezdxf.lldxf import const
import subprocess
import os
import numpy as np
import pandas as pd
import math
from itertools import combinations
from sympy import symbols, Matrix, Eq, solve
from dataclasses import dataclass
from backend.mathematical import Mathematical
from backend.guipresentation import presentation
from backend.datafiltration import datafiltration
from database.db_objects import object_db_results, validate_categories, dxf_mistake_block_explained, dxf_mistake_line_explained
from database.tolerance_config import extract_values_from_tolerance_sets, extract_boundary_values

maths = Mathematical()
pres = presentation() 
filter = datafiltration()

def autocad_points(filepath): 
    """This function extracts all necessasry data for analysis from the autocad file. 
       Inputs are filepath (the autocad file itself)
       Outputs are: Block references points, DiagonalBrace_Points (start and end position of all lines), All Walls (Wall points, points on the channel outline)"""

    doc = ezdxf.readfile(filepath)
    msp = doc.modelspace()
    
    block_length = []
    blocks = []
    Blockref_Points = []
    all_lines = []
    all_walls = []  
    insert_refs = []
    block_names = []
    new_names = []
    layers = []
    offsets = []
    wall_point_refs = [] 

    for insert in msp.query('INSERT'): 
        blockName = insert.dxf.name
        x = round(insert.dxf.insert.x, 2)
        y = round(insert.dxf.insert.y, 2)
        block_length.append([blockName, x, y]) 

    x_min, x_max, y_min, y_max = extract_boundary_values()
    blocks_fil = maths.blockcheck(block_length, x_min, x_max, y_min, y_max)

    for insert in msp.query('INSERT'): 
        blockName = insert.dxf.name
        x = round(insert.dxf.insert.x, 2)
        y = round(insert.dxf.insert.y, 2) 
        angle = round(insert.dxf.rotation, 2)

        if blockName.startswith('*U'): #Dynamic block
            block = doc.blocks.get(blockName)
            blockRecord = block.block_record
            try:
                if xdata := blockRecord.get_xdata("AcDbBlockRepBTag"):
                    for tag in xdata:
                        if tag.code == 1005: #xdata tag to store reference handle
                            ogHandle = tag.value
                            for b in doc.blocks: #Look through all blocks to find original reference block (handle match)
                                if b.dxf.handle == ogHandle:
                                    name = b.dxf.name #Use the name of the original block
                                    block_def = b  # *** NEW: Store block definition for offset calculation ***
            except const.DXFValueError: #Doesn't have indirect dynamic block tag or xdata not available
                print("Not a dynamic block")
                name = blockName
                block_def = block  # *** NEW: Use current block if not dynamic ***

        else: #Non-dynamic standard block
            name = blockName
            block_names.append([blockName, x, y])
            block_def = doc.blocks.get(blockName)  # *** NEW: Get block definition for standard blocks ***

        offset_found = False 
        name_error = None 

        bedit_check = len(blocks_fil)

        if bedit_check == 1: 
            if blockName != blocks_fil[0][0]:
                continue

            for entity in block_def:
                if entity.dxftype() == 'INSERT':
                    x_offset = entity.dxf.insert.x
                    y_offset = entity.dxf.insert.y
                    new_name = entity.dxf.name
                    offsets.append([new_name, x_offset, y_offset, name])

                    if new_name.startswith('*U'):
                        nested_block = doc.blocks.get(new_name)
                        nested_record = nested_block.block_record
                        try:
                            if xdata := nested_record.get_xdata("AcDbBlockRepBTag"):
                                for tag in xdata:
                                    if tag.code == 1005:
                                        ogHandle = tag.value
                                        for b in doc.blocks:
                                            if b.dxf.handle == ogHandle:
                                                new_name = b.dxf.name
                        except const.DXFValueError:
                            pass  

                    new_names.append([new_name])
                    x_final = round(x + x_offset, 2)
                    y_final = round(y + y_offset, 2)
                    if new_name != name:
                        name_error = True
                    if new_name == name:
                        name_error = None
                    insert_refs.append(entity)  
                    Blockref_Points.append([new_name, x_final, y_final, angle, name, entity])


                elif entity.dxftype() == 'LINE':
                    layer = entity.dxf.layer
                    start_x = round(x + entity.dxf.start.x, 2)
                    start_y = round(y + entity.dxf.start.y, 2)
                    end_x = round(x + entity.dxf.end.x, 2)
                    end_y = round(y + entity.dxf.end.y, 2)
                    layers.append([layer])
                    all_lines.append([layer, start_x, start_y, end_x, end_y, True, entity])

                elif entity.dxftype() == 'LWPOLYLINE':
                    if entity.dxf.layer == 'CHANNEL OUTLINE':   # add layer filter
                        wall_point_refs.append(entity)
                        raw_points = extract_polyline_points(entity)
                        offset_points = [
                            [round(x + p[0], 1), round(y + p[1], 1)]
                            for p in raw_points
                            if 10 <= x + p[0] <= 300000 and 10 <= y + p[1] <= 300000
                        ]
                        if offset_points:   # only append if not empty
                            all_walls.append(offset_points)


        else: 
            insert_refs.append(insert)
            for entity in block_def: #Searching for blocks inside the BEDIT
                if entity.dxftype() == 'INSERT':
                    x_offset = entity.dxf.insert.x   #find offset inside block 
                    y_offset = entity.dxf.insert.y
                    new_name = entity.dxf.name        #find 
                    new_names.append([new_name])
                    if x_offset > 0.01 and y_offset > 0.01:
                        x_final = x + x_offset 
                        y_final = y + y_offset 
                        offset_found = True 
                    if new_name != name: 
                        name_error = True 
                    if new_name == name: 
                        name_error = None 
         
            attrib_data = {}  #reset each iteration
            if insert.has_attrib:
                for attrib in insert.attribs:
                    attrib_data[attrib.dxf.tag] = attrib.dxf.text 
                
            if offset_found: 
                Blockref_Points.append([new_name, x_final, y_final, angle, name, insert])
            else:     
                Blockref_Points.append([name, x, y, angle, name_error, insert])  
        
    if bedit_check != 1: 
        for line in msp.query('LINE'):
            layer = line.dxf.layer
            name = blockName 
            start_x = round(line.dxf.start.x, 2)
            start_y = round(line.dxf.start.y, 2)
            end_x = round(line.dxf.end.x, 2)
            end_y = round(line.dxf.end.y, 2)
            layers.append([layer])
            all_lines.append([layer, start_x, start_y, end_x, end_y, False, line])    

        # Extract POLYLINE data 
        for polyline in msp.query('LWPOLYLINE[layer=="CHANNEL OUTLINE"]'):
            points = extract_polyline_points(polyline)
            wall_point_refs.append(polyline)
            all_walls.append(points)     

    if len(all_lines) < 1 or len(all_walls) < 1 or len(Blockref_Points) < 1: 
        return None 

    else: 
        #extracting set values 
        x_min, x_max, y_min, y_max = extract_boundary_values()
        block_tolerance, line_tolerance1, line_tolerance2 = extract_values_from_tolerance_sets()

        #filtering blocks and lines to ensure they are within the boundaries 
        filtered_lines = maths.filter_lines(all_lines, x_min, x_max, y_min, y_max)
        filtered_blockref, filtered_walls = maths.filter_blocks_walls(Blockref_Points, all_walls, x_min, x_max, y_min, y_max)

        #backend maths 
        wall_lengths = maths.wall_len(filtered_lines)  
        slopes, y_intercepts, line_properties, wall_slopes, wall_intercepts = maths.slope_values(filtered_lines, filtered_walls) 
        
        #Geometry Engine 
        (blocks_on_line, mistake_points, final_corrected_blocks,fixed_all_blocks, 
         bedit_mistake_points, bedit_corrected_blocks, 
         mistake_exp) = filter.On_Channel_Line(filtered_blockref, filtered_walls, line_properties, bedit_check, block_tolerance, tolerance2=5)

        on_line_points, all_lines_table = pres.what_line(blocks_on_line, filtered_walls, filtered_lines, tolerance = 1)

        (line_mistakes, correct_lines, 
         line_line_connections, line_line_connections_check) = filter.find_line_error(filtered_lines, all_walls, line_properties, wall_slopes, wall_intercepts, line_tolerance1, 25, line_tolerance2)
        
        fixed_lines, line_mistake_exp = filter.fix_line_mistakes(line_mistakes)

        bedit_lines= filter.filter_offset_lines(correct_lines, line_mistakes)

        line_duplicates = filter.flag_duplicate_lines(all_lines)

        #Gui 
        wall_slope_intercept = pres.combine_slope_walls(wall_lengths, slopes, y_intercepts) #for presentation in gui table 

        #Database 
        print(f'this is the line mistakes {len(line_mistakes)}')
        print(f'These are the correct lines {len(correct_lines)}')
        (post_accepted_blocks, post_accepted_lines,
        post_rejected_block, post_rejected_lines,
        blockname_unmatched, linename_unmatched) = object_db_results(fixed_all_blocks, filtered_blockref, all_lines, correct_lines, fixed_lines, wall_slopes, wall_intercepts, all_walls)

        line_block_connections = filter.link_line_block_connections(correct_lines, fixed_lines, fixed_all_blocks)

        final_line_line_connections = filter.find_line_line_connections(fixed_lines, wall_slopes, wall_intercepts, all_walls, line_line_connections_check, line_line_connections)

        line_name, all_fail = validate_categories(final_line_line_connections, line_block_connections)

        #mistake explainer 
        mistake_block_reason = dxf_mistake_block_explained(mistake_exp)
        mistake_line_reason = dxf_mistake_line_explained(line_mistake_exp)
 
        return (doc, on_line_points, all_lines_table, 
            wall_slope_intercept, filtered_walls, mistake_points, 
            final_corrected_blocks, line_mistakes, bedit_lines, 
            line_duplicates, post_accepted_blocks, post_accepted_lines, 
            post_rejected_block, post_rejected_lines, line_name, all_fail, 
            blocks_fil, bedit_check, fixed_lines, all_walls, wall_point_refs, bedit_mistake_points, bedit_corrected_blocks,
            mistake_block_reason, mistake_line_reason, blockname_unmatched, linename_unmatched)
    
def extract_polyline_points(polyline): #Convert wall points into x and y points 
        if polyline.dxftype() == 'LWPOLYLINE':
            wall_points = []
            for point in polyline.get_points():
                x = float(round(point[0], 1))  
                y = float(round(point[1], 1))  
                wall_points.append([x, y])
            return wall_points
        # return []

def update_dxf_in_place(filepath, output_filepath):
    """This function updates the dxf file, function updates Block reference and line positions based on corrections
    Red box is drawn around Block reference mistakes and a Red circle is drawn around line mistakes. """

    (doc, on_line_points, all_lines_table, 
        wall_slope_intercept, filtered_walls, mistake_points, 
        corrected_blocks, line_mistakes, bedit_lines,  
        duplicate_lines, _, _, post_rejected_block, 
        post_rejected_line, _, all_fail, blocks_fil, bedit_check, fixed_lines, all_walls, wall_point_refs, _, _,
        mistake_block_reason, mistake_line_reasons, blockname_unmatched, linename_unmathced) = autocad_points(filepath)
    
    msp = doc.modelspace()

    if 'PE_URL' not in doc.appids:
        doc.appids.new('PE_URL')

    if 'CORRECTION_HIGHLIGHT' not in doc.layers:
        correction_layer = doc.layers.new('CORRECTION_HIGHLIGHT')
        correction_layer.color = 1

    if len(blocks_fil) == 1:
        # For block references

        container_x = blocks_fil[0][1]
        container_y = blocks_fil[0][2]

        # For polylines (channel outline walls)
        for idx, wall_points in enumerate(all_walls):
            original_ref = wall_point_refs[idx]
            world_points = [
                (p[0], p[1])
                for p in wall_points
            ]
            msp.add_lwpolyline(world_points, close=True, dxfattribs={
                'layer': original_ref.dxf.layer,
            })

        bedit_block_map = {}
        for idx, block_data in enumerate(corrected_blocks):
            name, new_x, new_y, angle, name_error, block_ref = block_data
            if new_x is not None and new_y is not None:
                new_insert = msp.add_blockref(name, (new_x, new_y), dxfattribs={
                    'rotation': block_ref.dxf.rotation,
                    'layer': block_ref.dxf.layer,
                    'xscale': block_ref.dxf.get('xscale', 1),
                    'yscale': block_ref.dxf.get('yscale', 1),
                })
                for attrib in block_ref.attribs:
                    attrib_world_x = container_x + attrib.dxf.insert.x
                    attrib_world_y = container_y + attrib.dxf.insert.y
                    new_insert.add_attrib(
                        attrib.dxf.tag,
                        attrib.dxf.text,
                        (attrib_world_x, attrib_world_y),
                        dxfattribs={
                            'layer': attrib.dxf.layer,
                            'height': attrib.dxf.get('height', 1.0),
                            'rotation': attrib.dxf.get('rotation', 0),
                        }
                    )
                bedit_block_map[block_ref] = new_insert

        bedit_line_map = {}
        for idx, line_data in enumerate(bedit_lines):
            name, x_start, y_start, x_end, y_end, offset, line_ref = line_data
            copied = line_ref.copy()
            msp.add_entity(copied)
            copied.dxf.start = (x_start, y_start)
            copied.dxf.end = (x_end, y_end)
            bedit_line_map[line_ref] = copied

        explain_mistakes_dxf(msp, duplicate_lines, mistake_block_reason, mistake_line_reasons, post_rejected_block, post_rejected_line, all_fail, doc, bedit_line_map, bedit_block_map)

        # Delete the container INSERT
        for insert in msp.query('INSERT'):
            if insert.dxf.name == blocks_fil[0][0]:
                msp.delete_entity(insert)
                break

    else:
        explain_mistakes_dxf(msp, duplicate_lines, mistake_block_reason, mistake_line_reasons, post_rejected_block, post_rejected_line,
                             all_fail, doc, {}, {})

    doc.saveas(output_filepath)

def explain_mistakes_dxf(msp, duplicate_lines, mistake_block_reason, mistake_line_reasons, post_rejected_block, post_rejected_line, all_fail, doc, bedit_line_map, bedit_block_map):

    sep_duplicate_lines = create_separation(duplicate_lines, 'Duplicate')
    for i, line in enumerate(sep_duplicate_lines):  # flagging a duplicate line
        name, x_s, y_s, x_e, y_e, line_ref, reason = line
        triangle1 = draw_triangle(msp, x_s, y_s)
        triangle2 = draw_triangle(msp, x_e, y_e)
        resolved_line_ref = bedit_line_map.get(line_ref, line_ref)
        link_shape_line(resolved_line_ref, triangle1, triangle2, name, 'Duplicate', i, doc)
        draw_group_hyperlink(resolved_line_ref, reason, triangle1, triangle2, i)

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
        link_shape_line(resolved_block_ref, circle, None, name_b, 'Block', i, doc)
        draw_group_hyperlink(resolved_block_ref, reason, circle, None, i)
        
    for i, mistake_line in enumerate(mistake_line_reasons):
        name_l, x_l, y_l, line_ref, reason = mistake_line
        circle = msp.add_circle(center=(x_l, y_l), radius=75, dxfattribs={"color": 1})
        resolved_line_ref = bedit_line_map.get(line_ref, line_ref)
        link_shape_line(resolved_line_ref, circle, None, name_l, 'Geometry', i, doc)
        draw_group_hyperlink(resolved_line_ref, reason, circle, None, i)

    for i, block in enumerate(post_rejected_block):  #explaing why a rejected block from object database was rejected
        name, x, y, reason, block_ref = block 
        triangle = draw_triangle(msp, x, y)
        triangle.set_xdata('PE_URL', [(1000, ""),(1002, "{"),(1000, reason),(1000, ""),(1002, "}"),])
        resolved_block_ref = bedit_block_map.get(block_ref, block_ref)
        link_shape_line(resolved_block_ref, triangle, None, name, 'Object_DB_Block', i, doc)
        draw_group_hyperlink(resolved_block_ref, reason, triangle, None, i)

    seperation_lines = create_separation(all_fail, 'Category_db') #ensuring there is no overlap between triangles 0
    for i, seperation_line in enumerate(seperation_lines):
        line_name, x_start, y_start, line_start_category, x_end, y_end, line_end_category, reason, line_ref = seperation_line
        triangle1 = draw_triangle(msp, x_start, y_start)
        triangle2 = draw_triangle(msp, x_end, y_end)
        resolved_line_ref = bedit_line_map.get(line_ref, line_ref)
        link_shape_line(resolved_line_ref, triangle1, triangle2, line_name, 'Category', i, doc)  
        draw_group_hyperlink(resolved_line_ref, reason, triangle1, triangle2, i)

    sep_object_lines = create_separation(post_rejected_line, 'Object_db')
    for i, line in enumerate(sep_object_lines):   #why a rejected line from object database was rejected
        name, x_s, y_s, x_e, y_e, reason, line_ref = line     
        triangle1 = draw_triangle(msp, x_s, y_s)
        triangle2 = draw_triangle(msp, x_e, y_e)
        resolved_line_ref = bedit_line_map.get(line_ref, line_ref)
        link_shape_line(resolved_line_ref, triangle1, triangle2, name, 'Object', i, doc)
        draw_group_hyperlink(resolved_line_ref, reason, triangle1, triangle2, i)

 
def link_shape_line(ref, shape1, shape2, name, error_type, i, doc): 
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
              

def draw_group_hyperlink(ref, reason, shape1, shape2, i): 
    """Function for attaching a hyperlink to an error 
    the function attaches the hyperlink to the line and the shapes that flag the error"""
    xdata = [(1000, ""),(1002, "{"),(1000, reason),(1000, ""),(1002, "}"),]
    if shape1 is not None:
        shape1.set_xdata('PE_URL', xdata)
    if shape2 is not None:
        shape2.set_xdata('PE_URL', xdata)

    ref.set_xdata('PE_URL', [(1000, ""),(1002, "{"),(1000, reason),(1000, ""),(1002, "}"),])

            
def create_separation(lines, type):
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

            
def draw_red_box(msp, x, y, size):
    """Draws a red rectangle around corrected block references"""
    corners = [
        (x - size, y - size),
        (x + size, y - size),
        (x + size, y + size),
        (x - size, y + size),
    ]
    msp.add_lwpolyline(corners, close=True, dxfattribs={'layer': 'CORRECTION_HIGHLIGHT', 'color': 1})

def draw_triangle(msp, x, y): 
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

    
