# BiV-Me | CDT Personalization Pipeline

This repository is a component of the **Cardiac Digital Twin Personalization Pipeline** implemented for the Master Thesis: _"Implementation of a pipeline to generate a patient-specific Digital Twin of Cardiac Electrophysiology"_

For more details on the complete Pipeline refer to the main repository 

## Overview
This repository is a fork of the open-source **biv-me** framework originally developed by J.Dillon and C. Mauger from **UOA-Heart-Mechanics-Research** 

**biv-me** automates the reconstruction of 3D biventricular cardiac geometries from multi-view Cardiac Magnetic Resonance (CMR) DICOM images. 

Within the **Cardiac Digital Twin Personalization Pipeline** it is used to perform the **Anatomical Twinning** phase, converting raw patient CMR imaging into cardiac surfaces, then a 3D volumetric tetrahedral mesh is generated using **meshtool** to prepare for the next pipeline phases.

## Main modifications
To integrate the tool in the CDT Personalization Pipeline the original code was modified and adapted as follows:

- **Full Containerization**: creation of a Docker Container that includes all the required dependencies, including Python, Pytorch, pretrained deep learning models and a Jupyter Server.
- **Web Based View Correction GUI**: replaced the original desktop native GUI with a custom Web Interface using **Streamlit**, making it possible to access the interface from outside the Docker container. Using this GUI a user can review automated predictions and manually correct view labels.
- **Volumetric Mesh generation**: inclusion of the tool **meshtool** to generate a Volumetric Tetrahedral mesh from the three cardiac surfaces exported by biv-me.  

## Usage

## Acknowledgments
------------------------------------
The code in this repository is based on the open-source **biv-me** project originally developed by J.Dillon and C. Mauger from **UOA-Heart-Mechanics-Research** 

**Original Repository**: [UOA-Heart-Mechanics-Research/biv-me](https://github.com/UOA-Heart-Mechanics-Research/biv-me)

**Reference Publications**: 

- Dillon, J.R., Mauger, C., Zhao, D., Deng, Y., Petersen, S.E., McCulloch, A.D., Young, A.A., & Nash, M.P. An open-source end-to-end pipeline for generating 3D+t biventricular meshes from cardiac magnetic resonance imaging. In: Functional Imaging and Modeling of the Heart (FIMH) 2025 (pp. 372-383). LNCS 15673.  [DOI:10.1007/978-3-031-94562-5_34](https://doi.org/10.1007/978-3-031-94562-5_34)

- Mauger, C., Gilbert, K., Suinesiaputra, A., Pontre, B., Omens, J., McCulloch, A., & Young, A. (2018, July). An iterative diffeomorphic algorithm for registration of subdivision surfaces: application to congenital heart disease. In 2018 40th Annual International Conference of the IEEE Engineering in Medicine and Biology Society (EMBC) (pp. 596-599). IEEE. [DOI: 10.1109/EMBC.2018.8512394](https://doi.org/10.1109/EMBC.2018.8512394)

- Dillon Joshua R. et al. “An Open-Source End-to-End Pipeline for Generating
3D+t Biventricular Meshes from Cardiac Magnetic Resonance Imaging”.
In: Functional Imaging and Modeling of the Heart. Vol. 15673. Springer
Nature Switzerland, 2025, pp. 372–383. DOI: https://doi.org/10.1007/978-3-031-94562-5_34
