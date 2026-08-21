import ezdxf
from ezdxf.lldxf import const
from backend.mathematical import Mathematical
from backend.guipresentation import presentation
from backend.datafiltration import datafiltration
from backend.line_connections import line_connections
from backend.autocad_file_presentation import file_presentation
from database.db_objects import object_db_results, validate_categories, dxf_mistake_block_explained, dxf_mistake_line_explained
from database.tolerance_config import extract_values_from_tolerance_sets, extract_boundary_values
from backend.dataclasses.block_ref_data import BlockRef
from backend.dataclasses.line_data import Lines
from backend.dataclasses.autocadres import AnalysisResult

maths = Mathematical()
pres = presentation() 
filter = datafiltration()
l_conn = line_connections()
file_pres = file_presentation() 


def autocad_points(filepath): 
    """This function extracts all necessasry data for analysis from the autocad file. 
       Inputs are filepath (the autocad file itself)
       """

    doc = ezdxf.readfile(filepath)
    msp = doc.modelspace()
    
    blocks = []
    Blockref_Points = []
    all_lines = []
    all_walls = []  
    wall_point_refs = [] 

    #Serach the blocks initially to find out how many there are and to set the boundarys 
    for insert in msp.query('INSERT'): 
        blockName = insert.dxf.name
        x = round(insert.dxf.insert.x, 2)
        y = round(insert.dxf.insert.y, 2)
        angle = round(insert.dxf.rotation, 2)
        blocks.append([blockName, x, y]) 

    x_min, x_max, y_min, y_max = extract_boundary_values()
    blocks_fil = maths.blockcheck(blocks, x_min, x_max, y_min, y_max)
    bedit_check = len(blocks_fil)

    #Search all blocks again 
    for insert in msp.query('INSERT'): 
        blockName = insert.dxf.name
        x = round(insert.dxf.insert.x, 2)
        y = round(insert.dxf.insert.y, 2) 
        angle = round(insert.dxf.rotation, 2)

        if blockName.startswith('*U'): #Dynamic block
            name, block_def = resolve_block_name(doc, blockName, False)

        else: #Non-dynamic standard block
            name = blockName
            block_def = doc.blocks.get(blockName)  # *** NEW: Get block definition for standard blocks ***

        offset_found = False 
        name_error = None 

        #blocks and lines arn't sitting in the model space they are in the block definition
        # These all have to be looked for again here 
        if bedit_check == 1: #If there is only one block within the sketch (bedit error)
            if blockName != blocks_fil[0][0]:
                continue

            for entity in block_def:
                if entity.dxftype() == 'INSERT':
                    x_offset = entity.dxf.insert.x
                    y_offset = entity.dxf.insert.y
                    new_name = entity.dxf.name

                    if new_name.startswith('*U'):
                        new_name = resolve_block_name(doc, new_name, True)

                    x_final = round(x + x_offset, 2)
                    y_final = round(y + y_offset, 2)
                    if new_name != name:
                        name_error = True
                    if new_name == name:
                        name_error = None 
                    Blockref_Points.append(BlockRef(name=new_name, x=x_final, y=y_final, angle=angle, name_error=name, blockref=entity))

                elif entity.dxftype() == 'LINE':
                    layer = entity.dxf.layer
                    start_x = round(x + entity.dxf.start.x, 2)
                    start_y = round(y + entity.dxf.start.y, 2)
                    end_x = round(x + entity.dxf.end.x, 2)
                    end_y = round(y + entity.dxf.end.y, 2)
                    all_lines.append(Lines(name=layer, x_start=start_x, y_start=start_y, x_end=end_x, y_end=end_y, offset=True, lineref=entity))

                elif entity.dxftype() == 'LWPOLYLINE':
                    if entity.dxf.layer == 'CHANNEL OUTLINE':   # add layer filter
                        wall_point_refs.append(entity)
                        raw_points = extract_polyline_points(entity)
                        offset_points = [
                            [round(x + p[0], 1), round(y + p[1], 1)]
                            for p in raw_points
                        ]
                        if offset_points:   # only append if not empty
                            all_walls.append(offset_points)

        else: 
            for entity in block_def: #Searching for blocks inside the BEDIT
                if entity.dxftype() == 'INSERT':
                    x_offset = entity.dxf.insert.x   #find offset inside block 
                    y_offset = entity.dxf.insert.y
                    new_name = entity.dxf.name        #find 
                    if x_offset > 0.01 and y_offset > 0.01:
                        x_final = x + x_offset 
                        y_final = y + y_offset 
                        offset_found = True 
                    if new_name != name: 
                        name_error = True 
                    if new_name == name: 
                        name_error = None 
                
            if offset_found: #if a singular block is inside a bedit
                Blockref_Points.append(BlockRef(name=new_name, x=x_final, y=y_final, angle=angle, name_error=name, blockref=insert))
            else: #normal block 
                Blockref_Points.append(BlockRef(name=name, x=x, y=y, angle=angle, name_error=name_error, blockref=insert))
        
    if bedit_check != 1: #normal file situation 
        for line in msp.query('LINE'):
            layer = line.dxf.layer
            start_x = round(line.dxf.start.x, 2)
            start_y = round(line.dxf.start.y, 2)
            end_x = round(line.dxf.end.x, 2)
            end_y = round(line.dxf.end.y, 2)
            all_lines.append(Lines(name=layer, x_start=start_x, y_start=start_y, x_end=end_x, y_end=end_y, offset=False, lineref=line))   

        # Extract POLYLINE data 
        for polyline in msp.query('LWPOLYLINE[layer=="CHANNEL OUTLINE"]'):
            points = extract_polyline_points(polyline)
            wall_point_refs.append(polyline)
            all_walls.append(points)     

    return Blockref_Points, all_lines, all_walls, wall_point_refs, doc, blocks_fil, bedit_check        
    
def extract_polyline_points(polyline): #Convert wall points into x and y points 
    if polyline.dxftype() == 'LWPOLYLINE':
        wall_points = []
        for point in polyline.get_points():
            x = float(round(point[0], 1))  
            y = float(round(point[1], 1))  
            wall_points.append([x, y])
        return wall_points
    

def resolve_block_name(doc, blockName, bedit):
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
        if bedit: 
            return name  
        else: 
            return name, block_def   
                     
    except const.DXFValueError: #Doesn't have indirect dynamic block tag or xdata not available
        pass 

    
        
def dealing_with_everything(filepath): 

    Blockref_Points, all_lines, all_walls, wall_point_refs, doc, blocks_fil, bedit_check = autocad_points(filepath)

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
         mistake_exp) = filter.find_fix_block_errors(filtered_blockref, filtered_walls, line_properties, bedit_check, block_tolerance, tolerance2=5)
        on_line_points, all_lines_table = pres.what_line(blocks_on_line, filtered_walls, filtered_lines, tolerance = 1)
        (line_mistakes, correct_lines, 
         line_line_connections) = filter.find_line_error(filtered_lines, all_walls, line_properties, wall_slopes, wall_intercepts, line_tolerance1, 25, line_tolerance2)
        fixed_lines, line_mistake_exp = filter.fix_line_mistakes(line_mistakes)
        bedit_lines= filter.filter_offset_lines(correct_lines, line_mistakes)
        line_duplicates = filter.flag_duplicate_lines(filtered_lines)

        #Gui 
        wall_slope_intercept = pres.combine_slope_walls(wall_lengths, slopes, y_intercepts) #for presentation in gui table 

        #Database 
        (post_accepted_blocks, post_accepted_lines,
        post_rejected_block, post_rejected_lines,
        blockname_unmatched, linename_unmatched) = object_db_results(fixed_all_blocks, filtered_blockref, correct_lines, fixed_lines, wall_slopes, wall_intercepts, all_walls)
        line_block_connections = l_conn.link_line_block_connections(correct_lines, fixed_lines, line_mistakes, fixed_all_blocks)
        l_l_connections = l_conn.sort_line_block_line_conns(line_block_connections, line_line_connections)
        line_name, all_fail = validate_categories(l_l_connections, line_block_connections)

        #mistake explainer 
        mistake_block_reason = dxf_mistake_block_explained(mistake_exp)
        mistake_line_reason = dxf_mistake_line_explained(line_mistake_exp)
 

        return AnalysisResult(doc=doc, on_line_points=on_line_points, all_lines_table=all_lines_table,
            wall_slope_intercept=wall_slope_intercept, filtered_walls=filtered_walls, mistake_points=mistake_points,
            corrected_blocks=final_corrected_blocks, line_mistakes=line_mistakes, bedit_lines=bedit_lines,
            line_duplicates=line_duplicates, post_accepted_blocks=post_accepted_blocks, post_accepted_lines=post_accepted_lines,
            post_rejected_blocks=post_rejected_block, post_rejected_lines=post_rejected_lines, line_name=line_name,
            all_fail=all_fail, blocks_fil=blocks_fil, bedit_check=bedit_check, fixed_lines=fixed_lines,
            all_walls=all_walls, wall_point_refs=wall_point_refs, bedit_mistake_points=bedit_mistake_points,
            bedit_corrected_blocks=bedit_corrected_blocks, mistake_block_reason=mistake_block_reason,
            mistake_line_reason=mistake_line_reason, blockname_unmatched=blockname_unmatched, linename_unmatched=linename_unmatched,
        )


def update_dxf_in_place(filepath, output_filepath):
    """This function updates the dxf file, function updates Block reference and line positions based on corrections
    Red box is drawn around Block reference mistakes and a Red circle is drawn around line mistakes. """
   
    result = dealing_with_everything(filepath)

    doc = result.doc 
    corrected_blocks = result.corrected_blocks 
    bedit_lines = result.bedit_lines 
    duplicate_lines = result.line_duplicates
    post_rejected_block = result.post_rejected_blocks
    post_rejected_line = result.post_rejected_lines 
    all_fail = result.all_fail
    blocks_fil = result.blocks_fil
    all_walls = result.all_walls 
    wall_point_refs = result.wall_point_refs 
    mistake_block_reason = result.mistake_block_reason
    mistake_line_reasons = result.mistake_line_reason
    
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

        file_pres.explain_mistakes_dxf(msp, duplicate_lines, mistake_block_reason, mistake_line_reasons, post_rejected_block, post_rejected_line, all_fail, doc, bedit_line_map, bedit_block_map)

        # Delete the container INSERT
        for insert in msp.query('INSERT'):
            if insert.dxf.name == blocks_fil[0][0]:
                msp.delete_entity(insert)
                break

    else:
        file_pres.explain_mistakes_dxf(msp, duplicate_lines, mistake_block_reason, mistake_line_reasons, post_rejected_block, post_rejected_line,
                             all_fail, doc, {}, {})

    doc.saveas(output_filepath)