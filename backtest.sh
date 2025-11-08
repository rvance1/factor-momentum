#!/bin/bash

#SBATCH --time=02:00:00   # walltime
#SBATCH --ntasks=8   # number of processor cores (i.e. tasks)
#SBATCH --nodes=1   # number of nodes
#SBATCH --mem-per-cpu=20480M   # memory per CPU core
#SBATCH -J "run_fm_backtest"   # job name
#SBATCH --output=logs/factor_momentum_%j.out
#SBATCH --error=logs/factor_momentum_%j.err
#SBATCH --mail-user=boobus@byu.edu   # email address
#SBATCH --mail-type=BEGIN,END,FAIL


# LOAD MODULES, INSERT CODE, AND RUN YOUR PROGRAMS HERE

# Activate virtual environment
source /home/boobus/projects/factor_momentum/.venv/bin/activate

# Optional: load environment variables from .env manually (for safety)
export $(grep -v '^#' .env | xargs)

echo "Running backtest with Python from $(which python)"
echo "TMP is set to: $TMP"

# Run the Python script
python /home/boobus/projects/factor_momentum/backtest.py  