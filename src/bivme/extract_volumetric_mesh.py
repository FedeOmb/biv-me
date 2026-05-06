import sys
import os
import argparse
import numpy as np
import pyvista as pv
import vtk
import tetgen
import pymeshfix
import subprocess
from bivme import MODEL_RESOURCE_DIR

def fix_and_convert_vtk42(input_path, output_path):
    # Salvataggio
    print(f"Input surface mesh: {input_path}")
    surface = pv.read(input_path)

    surface = surface.triangulate()
   # surface = surface.clean(tolerance=1e-6)

   # print(f"Verifica e riparazione self-intersections per {os.path.basename(input_path)}...")
   # meshfix = pymeshfix.MeshFix(surface)
   # meshfix.repair(joincomp=True, remove_smallest_components=True)
   # surface = meshfix.mesh.clean(tolerance=1e-6)

   # edges = surface.extract_feature_edges(boundary_edges=True, non_manifold_edges=True)
  #  if edges.n_cells > 0:
 #       print(f"ATTENZIONE: Trovati {edges.n_cells} spigoli aperti, tento la chiusura...")
 #       surface = surface.fill_holes(hole_size=50)
 #       surface = surface.clean(tolerance=1e-6)

    writer = vtk.vtkPolyDataWriter()
    writer.SetInputData(surface)
    writer.SetFileName(output_path)
    writer.SetFileVersion(42)       # forza versione vtk 4.2
    writer.SetFileTypeToASCII()
    writer.Write()    
    print(f"Mesh superficie convertita in vtk 42 per meshtool: {output_path}")


def export_volumetric_mesh_meshtool(bivme_output_folder, casename, frame_num, output_filename):

    surface_filenames = [
        f"{casename}_EPICARDIAL_{frame_num:03d}",
        f"{casename}_LV_ENDOCARDIAL_{frame_num:03d}",
        f"{casename}_RV_ENDOCARDIAL_{frame_num:03d}"
    ]
    output_vtk42_paths = []

    for sur in surface_filenames:
        input_sur_path = os.path.join(bivme_output_folder, casename, 'vtk', sur+'.vtk')
        if not os.path.exists(input_sur_path):
            print(f"File di superficie non trovato: {input_sur_path}")
            return
        
        output_sur_path = os.path.join(bivme_output_folder, casename, 'vtk', sur + '_vtk42.vtk')
        fix_and_convert_vtk42(input_sur_path, output_sur_path)
        output_vtk42_paths.append(output_sur_path)

    output_vol_folder = os.path.join(bivme_output_folder, casename, 'volumetric')
    if not os.path.exists(output_vol_folder):
        os.makedirs(output_vol_folder)

    print("Generazione mesh volumetrica con meshtool...")
    surf_arg = ",".join(output_vtk42_paths)
    ins_tag_arg = "3,2,1"
    output_vol_path = os.path.join(bivme_output_folder, casename, 'volumetric', output_filename)
    cmd_vol = [
        "meshtool", "generate", "mesh",
        f"-surf={surf_arg}",
        f"-ins_tag={ins_tag_arg}",
        f"-outmsh={output_vol_path}",
        "-scale=1.0",
        "-ofmt=vtk_bin"
    ]
    output_resample_mesh = os.path.join(bivme_output_folder,casename,'volumetric', casename+'_1500mm')
    cmd_resample =[
        "meshtool", "resample", "mesh",
        f"-msh={output_vol_path}",
        f"-ifmt=vtk_bin",
        "-avrg=1.5",
        f"-outmsh={output_resample_mesh}",
        "-ofmt=vtk_bin"
    ] 
    
    try:
        print(f"Esecuzione comando: {' '.join(cmd_vol)}")
        subprocess.run(cmd_vol, check=True)
        print(f"Mesh volumetrica creata con successo in: {output_vol_path}")
        print(f"Esecuzione comando: {' '.join(cmd_resample)}")
        subprocess.run(cmd_resample, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Errore durante l'esecuzione di meshtool: {e}")
    except FileNotFoundError:
        print("Errore: meshtool non trovato")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Create volumetric mesh from biv-me surfaces using meshtool')
    parser.add_argument('--bivme_output_folder', type=str, required=True,
                        help='Cartella di output principale di biv-me (es. ../../output-sb)')
    parser.add_argument('--casename', type=str, required=True,
                        help='Nome del caso (es. sb3701)')
    parser.add_argument('--frame_num', type=int, default=0,
                        help='Numero del frame (default: 0)')
    parser.add_argument('--output_filename', type=str, required=True,
                        help='nome del file di output senza estensione')
    args = parser.parse_args()

    if not args.bivme_output_folder or not args.casename or not args.output_filename:
        args.bivme_output_folder = "../../output-sb"
        args.casename = "sb501"
        args.output_filename = "sb501_volmesh_meshtool"

    export_volumetric_mesh_meshtool(args.bivme_output_folder, args.casename, args.frame_num, args.output_filename)
