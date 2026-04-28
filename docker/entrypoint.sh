#!/usr/bin/env bash
set -e

source /opt/conda/etc/profile.d/conda.sh
conda activate bivme311

cd /biv-me

echo "Running entrypoint - installing biv-me dependancies..."
pip install -e .
# python src/pyezzi/setup.py build_ext --inplace

exec "$@"
