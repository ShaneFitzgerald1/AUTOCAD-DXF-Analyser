import ezdxf
from ezdxf.lldxf import const
import subprocess
import os
import numpy as np
import pandas as pd
import math
from sympy import symbols, Matrix, Eq, solve
from dataclasses import dataclass
from backend.mathematical import Mathematical
from backend.guipresentation import presentation
from backend.datafiltration import datafiltration
from database.db_objects import before_after, validate_categories, dxf_mistake_block_explained, dxf_mistake_line_explained

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
    line_refs = []
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

    blocks_fil = maths.blockcheck(block_length)

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
                    Blockref_Points.append([new_name, x_final, y_final, angle, name])


                elif entity.dxftype() == 'LINE':
                    line_refs.append(entity)
                    layer = entity.dxf.layer
                    start_x = round(x + entity.dxf.start.x, 2)
                    start_y = round(y + entity.dxf.start.y, 2)
                    end_x = round(x + entity.dxf.end.x, 2)
                    end_y = round(y + entity.dxf.end.y, 2)
                    layers.append([layer])
                    all_lines.append([layer, start_x, start_y, end_x, end_y, True])

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
                Blockref_Points.append([new_name, x_final, y_final, angle, name])
            else:     
                Blockref_Points.append([name, x, y, angle, name_error])  
        
    if bedit_check != 1: 
        for line in msp.query('LINE'):
            line_refs.append(line)
            layer = line.dxf.layer
            name = blockName 
            start_x = round(line.dxf.start.x, 2)
            start_y = round(line.dxf.start.y, 2)
            end_x = round(line.dxf.end.x, 2)
            end_y = round(line.dxf.end.y, 2)
            layers.append([layer])
            all_lines.append([layer, start_x, start_y, end_x, end_y, False])    

        # Extract POLYLINE data 
        for polyline in msp.query('LWPOLYLINE[layer=="CHANNEL OUTLINE"]'):
            points = extract_polyline_points(polyline)
            wall_point_refs.append(polyline)
            all_walls.append(points)     

    if len(all_lines) < 1 or len(all_walls) < 1 or len(Blockref_Points) < 1: 
        return None 

    else: 
        wall_lengths = maths.wall_len(all_lines)  
        slopes, y_intercepts, line_properties, wall_slopes, wall_intercepts = maths.slope_values(all_lines, all_walls) 
        wall_slope_intercept = pres.combine_slope_walls(wall_lengths, slopes, y_intercepts)
        (blocks_on_line, mistake_points, final_corrected_blocks,
        final_corrected_block_refs, filtered_walls, 
        correct_blocks, fixed_all_blocks, bedit_mistake_points,
        bedit_corrected_blocks, mistake_exp) = filter.On_Channel_Line(Blockref_Points, all_walls, insert_refs, line_properties, bedit_check, tolerance=1, tolerance_2=5)
        on_line_points, all_lines_table = pres.what_line(blocks_on_line, filtered_walls, all_lines, tolerance = 1)
        (line_mistakes, correct_lines, line_mistake_refs, 
        correct_line_refs, line_line_connections, line_line_connections_check) = filter.find_line_error(all_lines, all_walls, line_refs, line_properties, wall_slopes, wall_intercepts, tolerance=1)
        fixed_lines, fixed_lines_box, line_mistake_refs, line_mistake_exp = filter.fix_line_mistakes(line_mistakes, line_mistake_refs)

        (final_fixed_lines, final_correct_lines, 
         final_fixed_lines_refs, final_correct_line_refs) = filter.filter_offset_lines(line_mistake_refs, correct_lines, correct_line_refs, line_mistakes)

        line_mistake_points = filter.find_fixed_line_points(line_mistakes, fixed_lines_box)
        duplicate_line_refs, line_duplicate_points = filter.remove_duplicate_lines(all_lines, line_refs)

        filtered_blockref, filtered_walls, filtered_insert_refs  = maths.Shape_outline(Blockref_Points, all_walls, insert_refs)

        (post_accepted_blocks, post_accepted_lines, 
        post_rejected_block, post_rejected_lines,
        blockname_unmatched, linename_unmatched) = before_after(fixed_all_blocks, filtered_blockref, all_lines, correct_lines, fixed_lines, wall_slopes, wall_intercepts, all_walls, line_refs)

        line_block_connections = filter.link_line_connections(correct_lines, fixed_lines, fixed_all_blocks)

        final_line_line_connections = filter.fix_line_channel_return(fixed_lines, line_mistake_refs, wall_slopes, wall_intercepts, all_walls, line_line_connections_check, line_line_connections)

        line_name, all_fail = validate_categories(final_line_line_connections, line_block_connections)
        finals_corrected_blocks = maths.return_error(final_corrected_blocks, mistake_points)

        #mistake explainer 
        mistake_block_reason = dxf_mistake_block_explained(mistake_exp)
    
        mistake_line_reason = dxf_mistake_line_explained(line_mistake_exp)


        return (doc, on_line_points, all_lines_table, 
            wall_slope_intercept, filtered_walls, mistake_points, 
            finals_corrected_blocks, line_mistakes, final_fixed_lines, final_corrected_block_refs, 
            line_mistake_points, final_fixed_lines_refs, duplicate_line_refs, line_duplicate_points,
            post_accepted_blocks, post_accepted_lines, 
            post_rejected_block, post_rejected_lines, line_name, all_fail, 
            blocks_fil, bedit_check, fixed_lines, line_mistake_refs, 
            all_walls, wall_point_refs, bedit_mistake_points, bedit_corrected_blocks,
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
        corrected_blocks, line_mistakes, bedit_lines, corrected_block_refs, 
        line_mistake_points, line_bedit_refs, duplicate_line_refs, duplicate_line_points,
        _, _, post_rejected_block, post_rejected_line, _, all_fail, blocks_fil, bedit_check, fixed_lines, fixed_line_refs, all_walls, wall_point_refs, _, _,
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

        for idx, block_data in enumerate(corrected_blocks):
            name = block_data[0]
            new_x, new_y = block_data[1], block_data[2]
            original_ref = corrected_block_refs[idx]
            if new_x is not None and new_y is not None:
                new_insert = msp.add_blockref(name, (new_x, new_y), dxfattribs={
                    'rotation': original_ref.dxf.rotation,
                    'layer': original_ref.dxf.layer,
                    'xscale': original_ref.dxf.get('xscale', 1),
                    'yscale': original_ref.dxf.get('yscale', 1),
                })
                for attrib in original_ref.attribs:
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

        # For lines
        for idx, line_data in enumerate(bedit_lines):
            new_x_start, new_y_start = line_data[1], line_data[2]
            new_x_end, new_y_end = line_data[3], line_data[4]
            original_ref = line_bedit_refs[idx]
            copied = original_ref.copy()
            msp.add_entity(copied)
            copied.dxf.start = (new_x_start, new_y_start)
            copied.dxf.end = (new_x_end, new_y_end)

        for entity in duplicate_line_refs:
            msp.delete_entity(entity)        

        #Mistake explanation     

        explain_mistakes_dxf(msp, duplicate_line_points, mistake_block_reason, mistake_line_reasons, post_rejected_block, post_rejected_line, all_fail)

        # Delete the container INSERT
        for insert in msp.query('INSERT'):
            if insert.dxf.name == blocks_fil[0][0]:
                msp.delete_entity(insert)
                break
    
    else: 
        explain_mistakes_dxf(msp, duplicate_line_points, mistake_block_reason, mistake_line_reasons, post_rejected_block, post_rejected_line, all_fail)

    doc.saveas(output_filepath)

def explain_mistakes_dxf(msp, duplicate_line_points, mistake_block_reason, mistake_line_reasons, post_rejected_block, post_rejected_line, all_fail): 
    for line in duplicate_line_points:  # flagging a duplicate line 
            name, x_s, y_s, x_e, y_e, reason = line 
            triangle1 = draw_triangle(msp, x_s, y_s)
            triangle2 = draw_triangle(msp, x_e, y_e)
            triangle1.set_xdata('PE_URL', [(1000, ""),(1002, "{"),(1000, reason),(1000, ""),(1002, "}"),])
            triangle2.set_xdata('PE_URL', [(1000, ""),(1002, "{"),(1000, reason),(1000, ""),(1002, "}"),])

    for block in mistake_block_reason:
        name_b, x_b, y_b, reason = block
        circle = msp.add_circle(center=(x_b, y_b), radius=75, dxfattribs={"color": 1})
        circle.set_xdata('PE_URL', [
            (1000, ""),
            (1002, "{"),
            (1000, reason),
            (1000, ""),
            (1002, "}"),
        ])

    for mistake_line in mistake_line_reasons:
        name_l, x_l, y_l, reason = mistake_line
        circle = msp.add_circle(center=(x_l, y_l), radius=75, dxfattribs={"color": 1})
        circle.set_xdata('PE_URL', [
            (1000, ""),
            (1002, "{"),
            (1000, reason),
            (1000, ""),
            (1002, "}"),
        ])

    for block in post_rejected_block:  #explaing why a rejected block from object database was rejected
        name, x, y, reason = block 
        triangle = draw_triangle(msp, x, y)
        triangle.set_xdata('PE_URL', [(1000, ""),(1002, "{"),(1000, reason),(1000, ""),(1002, "}"),])

    for line in post_rejected_line:   #why a rejected line from object database was rejected
        name, x_s, y_s, x_e, y_e, reason = line     
        triangle1 = draw_triangle(msp, x_s, y_s)
        triangle2 = draw_triangle(msp, x_e, y_e)

        triangle1.set_xdata('PE_URL', [(1000, ""),(1002, "{"),(1000, reason),(1000, ""),(1002, "}"),])
        triangle2.set_xdata('PE_URL', [(1000, ""),(1002, "{"),(1000, reason),(1000, ""),(1002, "}"),])

    for line in all_fail: 
        line_name, x_start, y_start, line_start_category, x_end, y_end, line_end_category, reason = line  
        triangle1 = draw_triangle(msp, x_start, y_start)
        triangle2 = draw_triangle(msp, x_end, y_end)   

        triangle1.set_xdata('PE_URL', [(1000, ""),(1002, "{"),(1000, reason),(1000, ""),(1002, "}"),])
        triangle2.set_xdata('PE_URL', [(1000, ""),(1002, "{"),(1000, reason),(1000, ""),(1002, "}"),]) 


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
    displacement = 120
    point1 = x, y + displacement #90 degrees 
    point2 = x + displacement * math.cos(-0.523599), y + displacement * math.sin(-0.523599) # -30 degrees 
    point3 = x + displacement * math.cos(3.66519), y + displacement * math.sin(3.66519)   # -150 degrees 
    points = [point1, point2, point3]
    triangle = msp.add_lwpolyline(points, close=True, dxfattribs={'layer': 'CORRECTION_HIGHLIGHT', 'color': 1})

    return triangle 

    
