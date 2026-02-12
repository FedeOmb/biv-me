import os
import glob
import argparse
import numpy as np
import nibabel as nib
import pandas as pd
from pathlib import Path

def nifti_to_dicom_orientation(affine):
    """
    Converte la matrice affine NIfTI (RAS) in orientamento e posizione DICOM (LPS).
    """
    # NIfTI è RAS (Right, Anterior, Superior)
    # DICOM è LPS (Left, Posterior, Superior)
    # Conversione: Invertire X e Y
    
    # Matrice di conversione RAS -> LPS
    M_conv = np.diag([-1, -1, 1, 1])
    
    # Nuova affine in spazio LPS
    affine_lps = np.dot(M_conv, affine)
    
    # Estrazione Pixel Spacing (norma delle colonne dei vettori direzione)
    spacing_x = np.linalg.norm(affine_lps[:3, 0])
    spacing_y = np.linalg.norm(affine_lps[:3, 1])
    # spacing_z = np.linalg.norm(affine_lps[:3, 2]) # Spessore slice
    
    # Estrazione Cosine di Direzione (normalizzati)
    r_x = affine_lps[:3, 0] / spacing_x
    r_y = affine_lps[:3, 1] / spacing_y
    
    # Image Orientation Patient (6 valori: X_x, X_y, X_z, Y_x, Y_y, Y_z)
    image_orientation = np.concatenate([r_x, r_y])
    
    # Image Position Patient (Origine)
    origin = affine_lps[:3, 3]
    
    return origin, image_orientation, np.array([spacing_x, spacing_y])

def process_mnm2_case(case_dir, output_root):
    case_name = os.path.basename(case_dir)
    print(f"Processando caso: {case_name}")
    
    # Cartella di output specifica per il caso
    case_output_dir = os.path.join(output_root, case_name)
    images_output_dir = os.path.join(case_output_dir, "images")
    os.makedirs(images_output_dir, exist_ok=True)
    
    slice_info_data = []
    
    # Mappatura file M&M2 -> Viste biv-me
    # M&M2 usa: LA_CINE (solitamente 4ch), SA_CINE (SAX)
    file_map = {
        "SA_CINE.nii.gz": "SAX",
        "LA_CINE.nii.gz": "4ch" 
    }
    
    for filename, view_name in file_map.items():
        nifti_path = os.path.join(case_dir, filename)
        if not os.path.exists(nifti_path):
            print(f"  Attenzione: {filename} non trovato per {case_name}")
            continue
            
        img = nib.load(nifti_path)
        data = img.get_fdata()
        affine = img.affine
        
        # M&M2 CINE sono 4D: (X, Y, Z, Time)
        # Se Z > 1, è uno stack (es. SAX). Se Z=1, è una singola slice (es. 4ch).
        
        num_z = data.shape[2]
        
        for z in range(num_z):
            # Calcola l'affine per questa specifica slice Z
            # Spostiamo l'origine lungo l'asse Z dell'affine originale
            # P_new = P_old + z * colonna_Z
            slice_affine = affine.copy()
            z_shift = affine[:3, 2] * z
            slice_affine[:3, 3] += z_shift
            
            origin, orientation, spacing = nifti_to_dicom_orientation(slice_affine)
            
            # Salva la slice come singolo file NIfTI 3D (X, Y, Time)
            # biv-me si aspetta file separati per slice per gestire i metadati
            slice_data = data[:, :, z, :] # (X, Y, Time)
            
            # Creiamo un nome file univoco
            slice_filename = f"{view_name}_{z:02d}.nii.gz"
            output_path = os.path.join(images_output_dir, slice_filename)
            
            # Salviamo il NIfTI (mantenendo l'affine originale per coerenza visiva nei viewer, 
            # ma i metadati nel txt saranno convertiti per biv-me)
            # Nota: biv-me usa l'affine nel txt per il fitting, ma il nifti per la segmentazione.
            new_img = nib.Nifti1Image(slice_data, slice_affine)
            nib.save(new_img, output_path)
            
            # Aggiungi info al dataframe
            # Formato tipico SliceInfoFile: Filename, View, Group (uguale a view), ecc.
            # Nota: biv-me usa colonne specifiche. Adattiamo in base a GPDataSet.
            
            row = {
                'Slice ID': slice_filename,
                'View': view_name,
                'Group': view_name, # Spesso ridondante
                'Time Frames': slice_data.shape[2],
                'Image Position Patient': " ".join(map(str, origin)),
                'Image Orientation Patient': " ".join(map(str, orientation)),
                'Pixel Spacing': " ".join(map(str, spacing)),
                'Path': output_path
            }
            slice_info_data.append(row)

    # Creazione SliceInfoFile.txt
    if slice_info_data:
        df = pd.DataFrame(slice_info_data)
        # Ordine colonne importante per biv-me parsing
        # Solitamente biv-me usa un parsing custom o pandas. 
        # Salviamo in formato CSV con separatore tab o virgola.
        # Guardando il codice fornito, biv-me usa spesso pandas per leggere.
        
        output_csv = os.path.join(case_output_dir, "SliceInfoFile.txt")
        df.to_csv(output_csv, index=False, sep=',') 
        print(f"  Creato {output_csv}")

def main():
    parser = argparse.ArgumentParser(description="Converti M&M2 NIfTI in formato biv-me")
    parser.add_argument("-i", "--input", required=True, help="Cartella contenente i casi M&M2 (es. Training/Labeled)")
    parser.add_argument("-o", "--output", required=True, help="Cartella di output (es. src/output)")
    args = parser.parse_args()

    # Struttura M&M2 tipica: Cartella/Case01/file.nii.gz
    cases = [d for d in glob.glob(os.path.join(args.input, "*")) if os.path.isdir(d)]
    
    for case in cases:
        process_mnm2_case(case, args.output)

if __name__ == "__main__":
    main()
