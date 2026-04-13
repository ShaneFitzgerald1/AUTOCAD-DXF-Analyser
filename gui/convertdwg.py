import ezdxf
from ezdxf.lldxf import const
import subprocess
import os
import numpy as np
import pandas as pd
import math
import json5

###----NOTES ON DWG CONVERSION----###
"""
    # 'teighaConvPath' is the location where the Teigha Converter app is stored on your computer
    # It is necessary to download this app in order to convert standard .dwg files to .dxf so that the ezdxf library can be used to extract autocad info
    # Other two params specify the input .dwg filepath as well as the wanted .dxf output filepath
    # For simplicity, this output file will have the same name as the input and will be used to define the module name and number. Need to dicuss file naming (Although modNum/Name can be changed manually in the GUI interface)

"""
def convertDWG_DXF(dwgFolderpath, dxfFolderpath, teighaConvPath):

    dwgFolderpath = os.path.abspath(dwgFolderpath)
    dxfFolderpath = os.path.abspath(dxfFolderpath)
    os.makedirs(dxfFolderpath, exist_ok=True)

    # Find all DWG files in the input folder
    dwg_files = [f for f in os.listdir(dwgFolderpath) if f.lower().endswith('.dwg')]
    if not dwg_files:
        print('No DWG files found in input folder.')
        return None

    # ODA outputs DXF with same filename, just different extension
    dwg_filepaths = [os.path.join(dwgFolderpath, f) for f in dwg_files]
    dxf_filepaths = [os.path.join(dxfFolderpath, os.path.splitext(f)[0] + '.dxf') for f in dwg_files]

    #Construct command line command
    Command = [
        teighaConvPath,
        dwgFolderpath,
        dxfFolderpath, 'ACAD2018', 'DXF', '0', '1', '*.dwg'
    ]

    #Run the command hidden in the background
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    try:
        subprocess.run(Command, check=True, startupinfo=startupinfo)
        return dxf_filepaths
        
    except subprocess.CalledProcessError as Err:
        print(f"Conversion error: {Err}")
        return #Error occurred
    

def convertDXF_DWG(dxfFolderpath, dwgFolderpath, teighaConvPath):

    dxfFolderpath = os.path.abspath(dxfFolderpath)
    dwgFolderpath = os.path.abspath(dwgFolderpath)
    os.makedirs(dwgFolderpath, exist_ok=True)

    # Find all DXF files in the input folder
    dxf_files = [f for f in os.listdir(dxfFolderpath) if f.lower().endswith('.dxf')]
    if not dxf_files:
        print('No DXF files found in input folder.')
        return None

    # ODA outputs DWG with same filename, just different extension
    dwg_filepaths = [os.path.join(dwgFolderpath, os.path.splitext(f)[0] + '.dwg') for f in dxf_files]

    #Construct command line command
    Command = [
        teighaConvPath,
        dxfFolderpath,
        dwgFolderpath, 'ACAD2018', 'DWG', '0', '1', '*.dxf'
    ]

    #Run the command hidden in the background
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    try:
        subprocess.run(Command, check=True, startupinfo=startupinfo)
        return dwg_filepaths

    except subprocess.CalledProcessError as Err:
        print(f"Conversion error: {Err}")
        return None


# filepath = convertDXF_DWG(r'C:\Testingdxfs', r'C:\Testingdxfs', r'C:\Program Files\ODA\ODAFileConverter 26.12.0\ODAFileConverter.exe')
# print(f'this is the filepath {filepath}')