import sys, tempfile, shutil, os 
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QGridLayout, QTableWidget, QLabel, QSizePolicy, QHeaderView, QMessageBox, QFileDialog, QTableWidgetItem, QPushButton, QHBoxLayout, QTabWidget
from backend.autocorrect import update_dxf_in_place
from backend.convertdwg import convertDWG_DXF, convertDXF_DWG



"""This file creates functions that output functions as speicfic type: DWG or DXF"""

def dwg_output(original_filepath, dxf_filepath, temp_dir, oda_dir, op_filetype):
    try:
        original_folder = os.path.dirname(original_filepath)

        if temp_dir is None: #dxf import
            output_filepath, _ = QFileDialog.getSaveFileName(None, "View DWG File Issues",
                    original_filepath.replace('.dxf', '_potential_issues.dwg'),"DWG Files (*.dwg)")
            if not output_filepath:
                return
            temp_dir = tempfile.mkdtemp()
            filename = os.path.basename(dxf_filepath)
            temp_filepath = os.path.join(temp_dir, filename)
            # Write annotated DXF into temp copy, not over the original
            update_dxf_in_place(dxf_filepath, temp_filepath)

        else: #dwg import
            if op_filetype == 'DWG':
                output_filepath, _ = QFileDialog.getSaveFileName(None, "View DWG File Issues",
                    original_filepath.replace('.dwg', '_potential_issues.dwg'),"DWG Files (*.dwg)")
            if op_filetype == 'DXF':
                output_filepath, _ = QFileDialog.getSaveFileName(None, "View DWG File Issues",
                    original_filepath.replace('.dwg', '_potential_issues.dxf'),"DXF Files (*.dxf)")
            if not output_filepath:
                return
            update_dxf_in_place(dxf_filepath, dxf_filepath)

        if op_filetype == 'DWG': 
            file_path = convertDXF_DWG(temp_dir, temp_dir, oda_dir)

        if op_filetype == 'DXF':
            file_path = [dxf_filepath]  


        temp_filepath = file_path[0] #setting the temporary dwg filepath
        file_name = os.path.basename(temp_filepath) #find the file name itself module20.dwg
        name = os.path.splitext(file_name)[0] #remove the dwg at the end, add manually to adjust name 

        if op_filetype == 'DWG':
            final_file_name = name + '_potential_issues.dwg'

        if op_filetype == 'DXF': 
            final_file_name = name + '_potential_issues.dxf'

        destination = os.path.join(original_folder, final_file_name)
        shutil.move(temp_filepath, destination)
        QMessageBox.information(None, "Success", f"Potential mistakes saved to:\n{output_filepath}")    
    except Exception as e: 
        QMessageBox.critical(None, "Error", f"Failed to create file:\n{str(e)}")