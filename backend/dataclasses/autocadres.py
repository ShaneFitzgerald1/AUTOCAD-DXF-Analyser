from dataclasses import dataclass
from typing import Any

@dataclass
class AnalysisResult:
    doc: Any
    #Gui Table presentation 
    on_line_points: list
    all_lines_table: list
    wall_slope_intercept: list

    #Blocks 
    filtered_walls: list
    mistake_points: list
    corrected_blocks: list
    mistake_block_reason: list
    
    #Walls 
    all_walls: list
    wall_point_refs: list

    #Lines 
    line_mistakes: list
    line_duplicates: list
    fixed_lines: list
    mistake_line_reason: list

    #Object Database 
    post_accepted_blocks: list
    post_accepted_lines: list
    post_rejected_blocks: list
    post_rejected_lines: list
    blockname_unmatched: list
    linename_unmatched: list

    #Category Database 
    line_name: list
    all_fail: list

    #Bedit Checking 
    blocks_fil: list
    bedit_check: int
    bedit_mistake_points: list
    bedit_corrected_blocks: list
    bedit_lines: list

