FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV CONDA_DIR=/opt/conda 
ENV PATH=/opt/conda/bin:$PATH
ENV CONDA_PLUGINS_AUTO_ACCEPT_TOS=True
ARG OPENCARP_BINARY=opencarp-v18.1.deb

# Sistema + librerie GUI (Tkinter + X11)
RUN apt-get update && apt-get install -y \
    wget bzip2 ca-certificates git build-essential \
    python3 python3-testresources python-is-python3 \
    libgl1 libglib2.0-0 \
    libx11-6 libxext6 libxrender1 libsm6 libice6 tk \
    && apt-get clean && apt-get autoremove \
    && rm -rf /var/lib/apt/lists/*

#download e installazione opencarp
RUN wget -q https://git.opencarp.org/api/v4/projects/16/packages/generic/opencarp-linux/v18.1/${OPENCARP_BINARY} \
    && apt-get update \
    && apt-get install -y ./${OPENCARP_BINARY} \
    && rm ${OPENCARP_BINARY} \
    && rm -rf /var/lib/apt/lists/*

# Miniconda
RUN wget -qO /tmp/miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
 && bash /tmp/miniconda.sh -b -p $CONDA_DIR \
 && rm /tmp/miniconda.sh \
 && $CONDA_DIR/bin/conda init bash \
 && $CONDA_DIR/bin/conda create -y -n bivme311 python=3.11 pip tk \
 && conda clean -afy

RUN conda run -n bivme311 pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu \
&& conda run -n bivme311 pip install nnunetv2

WORKDIR /biv-me
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"] 
CMD ["bash"]