import sys
import os
import argparse
import numpy as np
import pyvista as pv
import vtk
from pathlib import Path
from scipy.spatial import cKDTree

from bivme.fitting.BiventricularModel import BiventricularModel
from bivme.meshing.hex_mesh_functions import extract_sudivided_hex_mesh
from bivme.meshing.mesh import Mesh
from bivme import MODEL_RESOURCE_DIR


def export_volumetric_mesh(model_path, output_filename, subdivision_level=2, thetrahedral=True):
    """
    Carica un modello fittato biv-me ed esporta la mesh volumetrica esaedrica.
    """
    # 1. Inizializza il modello base (carica le matrici template)
    # Nota: BiventricularModel si aspetta che le risorse siano nella cartella corretta
    # Potresti dover aggiustare il path delle risorse se non lo trova
    biv_model = BiventricularModel(MODEL_RESOURCE_DIR, build_mode=True) 
    
    # 2. Carica i punti di controllo fittati dal file txt
    # Il file ha solitamente 388 righe (num nodi di controllo) e 3 colonne
    try:
        fitted_control_points = np.loadtxt(model_path, delimiter=',', skiprows=1, usecols=[0, 1, 2]).astype(np.float16)
    except Exception as e:
        print(f"Errore caricamento file {model_path}: {e}")
        return

    # Aggiorna il modello con i nuovi punti
    #biv_model.control_mesh = fitted_control_points
    biv_model.update_control_mesh(fitted_control_points)
    
    # 3. Genera la mesh esaedrica suddivisa  
    # La funzione 'extract_sudivided_hex_mesh' in hex_mesh_functions.py prende:
    # control_mesh, new_nodes_position, xi_coords, node_elem_map
    control_mesh_obj = Mesh("control_mesh")
    control_mesh_obj.set_nodes(biv_model.control_mesh)
    control_mesh_obj.set_elements(biv_model.control_et_indices)

    print("Generazione mesh volumetrica...")
    # Usiamo i dati "embedded" del modello per guidare la suddivisione
    hex_mesh = extract_sudivided_hex_mesh(
        control_mesh_obj,  # Mesh di controllo (nodi + elementi)
        biv_model.et_pos,  # Posizioni superficiali (guidano la forma)
        biv_model.et_vertex_xi, 
        biv_model.et_vertex_element_num
    )
    if subdivision_level > 0:
        # Se vuoi aumentare la risoluzione, hex_mesh_functions ha opzioni per suddividere ancora
        print(f"Aumento risoluzione mesh (subdivision level {subdivision_level})...")
        sub_hex_mesh = hex_mesh.subdivide_linear_interpolation_hex(subdivision_level)
        hex_mesh = sub_hex_mesh
  
    # 4. Assign Tags
    print("Assigning surface tags...")
    tree = cKDTree(hex_mesh.nodes)
    tags = np.zeros(hex_mesh.nodes.shape[0], dtype=int)
    
    # Map indices from BiventricularModel to Tags
    # 1: LV Endo, 2: RV Endo (Septum+Freewall), 3: Epi, 4: Base/Valves
    surface_map = {
        0: 1, # LV_ENDOCARDIAL
        1: 2, # RV_SEPTUM
        2: 2, # RV_FREEWALL
        3: 3, # EPICARDIAL
        4: 4, 5: 4, 6: 4, 7: 4, 8: 4 # Valves/Base
    }
    
    for surf_idx, tag in surface_map.items():
        start, end = biv_model.et_vertex_start_end[surf_idx]
        surf_points = biv_model.et_pos[start:end+1]
        
        # Find corresponding nodes in hex_mesh
        dists, ids = tree.query(surf_points)
        mask = dists < 1e-4 # Tolerance for matching
        tags[ids[mask]] = tag
    
    # 4. Esportazione in VTK (Unstructured Grid)
    points = hex_mesh.nodes
    elements = hex_mesh.elements.copy() # Questi sono indici a 8 nodi (esaedri)
    
    ## Correzione ordinamento indici per VTK
    vtk_permutation = [0,1,3,2,4,5,7,6]
    elements = elements[:, vtk_permutation]

    # Creazione griglia PyVista
    # Cella tipo 12 = VTK_HEXAHEDRON
    cell_type = np.full(elements.shape[0], 12, dtype=np.uint8)
    
    # PyVista richiede che la lista celle inizi con il numero di punti per cella (8)
    cells = np.hstack((np.full((elements.shape[0], 1), 8), elements))
    cells = cells.flatten().astype(np.int32) # Appiattisci per formato VTK
    grid = pv.UnstructuredGrid(cells, cell_type, points)

    if thetrahedral:
        print("Converting to tetrahedral mesh...")
        grid = grid.triangulate()
    
    grid.point_data["SurfaceTag"] = tags
    # Salvataggio
    #grid.save(output_filename)
    writer = vtk.vtkUnstructuredGridWriter()
    writer.SetInputData(grid)
    writer.SetFileName(output_filename)
    writer.SetFileVersion(42)       # forza versione vtk 4.2
    writer.SetFileTypeToASCII()
    writer.Write()    
    print(f"Mesh volumetrica salvata in: {output_filename}")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Create volumetric mesh from fitted model')
    parser.add_argument('--input_model_path', type=str,
                        help='complete path to the fitted model file (e.g., 502_model_frame_000.txt)')
    parser.add_argument('--output_vtk_path', type=str,
                        help='complete path to the output VTK file (e.g., 502_volumetric_mesh_frame_000.vtk)')
    args = parser.parse_args()

    if not args.input_model_path or not args.output_vtk_path:
        args.input_model_path = "../output/503/503_model_frame_000.txt"
        args.output_vtk_path = "../output/503/503_volumetric_mesh_frame0_tetra_sub2.vtk"
    
    if os.path.exists(args.input_model_path):
        export_volumetric_mesh(args.input_model_path, args.output_vtk_path, subdivision_level=2)
    else:
        print("File di input non trovato. Esegui prima il fitting con biv-me.")