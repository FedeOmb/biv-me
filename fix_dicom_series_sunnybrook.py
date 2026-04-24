import pydicom
import numpy as np
import os

def get_plane_type(ds):    
    desc = ds.get("SeriesDescription", "").lower()
    if "4ch" in desc or "hla" in desc: return "4CH"
    if "2ch" in desc or "vla" in desc: return "2CH"
    
    # Calcolo geometrico se la descrizione è ambigua
    if "ImageOrientationPatient" in ds:
        iop = np.array(ds.ImageOrientationPatient, dtype=float)
        # I primi 3 sono il vettore riga, gli ultimi 3 il vettore colonna
        row_vec = iop[:3]
        col_vec = iop[3:]
        
        # Prodotto vettoriale per ottenere la normale al piano
        normal_vec = np.cross(row_vec, col_vec)
        
        # Prendiamo il valore assoluto della componente Z (indice 2)
        abs_z = abs(normal_vec[2])
        
        # SOGLIA EMPIRICA: 
        # Le viste 4CH sono più "orizzontali" (tipo assiali), quindi hanno Z alto (>0.5).
        # Le viste 2CH sono "verticali", quindi hanno Z basso (<0.5).
        if abs_z > 0.5:
            return "LAX_4Ch"
        else:
            return "LAX_2Ch"
            
    return "Sconosciuto"

def verify_series_by_orientation(dataset_dir):
    for root, dirs, files in os.walk(dataset_dir):
        for file in files:
            if file.endswith(".dcm"):
                path = os.path.join(root, file)
                ds = pydicom.dcmread(path, stop_before_pixels=True)
                tipo = get_plane_type(ds)
                print(f"{os.path.basename(root)} -> {tipo}")
                break

def fix_series_description(series_dir, type):
    for root, dirs, files in os.walk(series_dir):
        for file in files:
            if file.endswith(".dcm"):
                path = os.path.join(root, file)
                ds = pydicom.dcmread(path)
                # modifica solo le serie CINELAX
                if "CINELAX" in ds.get("SeriesDescription", "").upper():
                    if type in ["LAX_4Ch", "LAX_2Ch"]:
                        print(f"Modifica {path}: {ds.SeriesDescription} -> {type}")
                        ds.SeriesDescription = type
                        ds.save_as(path)

if __name__ == "__main__":
    root_dir = os.path.join(".", "sunnybrook", "dicoms", "sb901")
    verify_series_by_orientation(root_dir)

"""     series_dir = os.path.join(root_dir, "CINELAX_7")
    fix_series_description(series_dir, "LAX_4Ch")
    series_dir = os.path.join(root_dir, "CINELAX_8")
    fix_series_description(series_dir, "LAX_2Ch")  """