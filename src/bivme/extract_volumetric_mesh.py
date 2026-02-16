import sys
import os
import argparse
import numpy as np
import pyvista as pv
from pathlib import Path

from bivme.fitting.BiventricularModel import BiventricularModel
from bivme.meshing.hex_mesh_functions import extract_sudivided_hex_mesh
from bivme.meshing.mesh import Mesh
from bivme import MODEL_RESOURCE_DIR


def export_volumetric_mesh(model_path, output_filename, subdivision_level=2):
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
    
    # Se vuoi aumentare la risoluzione, hex_mesh_functions ha opzioni per suddividere ancora
    # sub_hex_mesh = hex_mesh.subdivide_linear_interpolation_hex(subdivision_level)
    
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
    
    # Salvataggio
    grid.save(output_filename)
    print(f"Mesh volumetrica salvata in: {output_filename}")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Create volumetric mesh from fitted model')
    parser.add_argument('--input_model_path', type=str,
                        help='complete path to the fitted model file (e.g., 502_model_frame_000.txt)')
    parser.add_argument('--output_vtk_path', type=str,
                        help='complete path to the output VTK file (e.g., 502_volumetric_mesh_frame_000.vtk)')
    args = parser.parse_args()

    #input_model_file = "../output/502/502_model_frame_000.txt"
    #output_vtk = "../output/502/502_volumetric_mesh_frame_000.vtk"
    
    if os.path.exists(args.input_model_path):
        export_volumetric_mesh(args.input_model_path, args.output_vtk_path)
    else:
        print("File di input non trovato. Esegui prima il fitting con biv-me.")