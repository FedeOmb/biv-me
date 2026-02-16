import sys
import os
import numpy as np
import pyvista as pv
from pathlib import Path

# Assicurati di essere nella root di biv-me o aggiungi il path
#sys.path.append(os.path.join(os.path.dirname(__file__), 'bivme'))

from bivme.fitting.BiventricularModel import BiventricularModel
from bivme.meshing.hex_mesh_functions import extract_sudivided_hex_mesh

def export_volumetric_mesh(model_path, output_filename, subdivision_level=2):
    """
    Carica un modello fittato biv-me ed esporta la mesh volumetrica esaedrica.
    """
    # 1. Inizializza il modello base (carica le matrici template)
    # Nota: BiventricularModel si aspetta che le risorse siano nella cartella corretta
    # Potresti dover aggiustare il path delle risorse se non lo trova
    biv_model = BiventricularModel() 
    
    # 2. Carica i punti di controllo fittati dal file txt
    # Il file ha solitamente 388 righe (num nodi di controllo) e 3 colonne
    try:
        fitted_control_points = np.loadtxt(model_path)
    except Exception as e:
        print(f"Errore caricamento file {model_path}: {e}")
        return

    # Aggiorna il modello con i nuovi punti
    biv_model.control_mesh = fitted_control_points
    
    # 3. Genera la mesh esaedrica suddivisa
    # extract_sudivided_hex_mesh richiede:
    # - control_mesh (il nostro oggetto)
    # - new_nodes_position (i nodi fittati espansi - qui usiamo quelli del modello)
    # - xi_coords (coordinate locali)
    # - node_elem_map (mappa nodi-elementi)
    
    # Nota: BiventricularModel ha internamente et_pos, et_vertex_xi, et_vertex_element_num
    # che vengono ricalcolati quando si aggiorna la control mesh? 
    # In biv-me potrebbe essere necessario ricalcolare le superfici prima, 
    # ma per la mesh HEX pura, usiamo la funzione di suddivisione diretta.
    
    # La funzione 'extract_sudivided_hex_mesh' in hex_mesh_functions.py prende:
    # control_mesh, new_nodes_position, xi_coords, node_elem_map
    
    # Hack: passiamo direttamente i dati che la funzione si aspetta
    # La funzione interna farà la suddivisione lineare degli esaedri
    
    print("Generazione mesh volumetrica...")
    # Usiamo i dati "embedded" del modello per guidare la suddivisione
    hex_mesh = extract_sudivided_hex_mesh(
        biv_model, 
        biv_model.et_pos,  # Posizioni superficiali (guidano la forma)
        biv_model.et_vertex_xi, 
        biv_model.et_vertex_element_num
    )
    
    # Se vuoi aumentare la risoluzione, hex_mesh_functions ha opzioni per suddividere ancora
    # sub_hex_mesh = hex_mesh.subdivide_linear_interpolation_hex(subdivision_level)
    
    # 4. Esportazione in VTK (Unstructured Grid)
    points = hex_mesh.nodes
    elements = hex_mesh.elements # Questi sono indici a 8 nodi (esaedri)
    
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
    input_model_file = "example/fitted-models/default/patient1/patient1_model_frame_000.txt"
    output_vtk = "patient1_volumetric_ED.vtk"
    
    if os.path.exists(input_model_file):
        export_volumetric_mesh(input_model_file, output_vtk)
    else:
        print("File di input non trovato. Esegui prima il fitting con biv-me.")