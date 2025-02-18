#!/bin/bash
# base for most cvmfs packages
ABASE=/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase/x86_64

# gcc 4.9
GCC_BASE=${ABASE}/Gcc/gcc493_x86_64_slc6/slc6/gcc49
GCC_BIN=${GCC_BASE}/bin
export PATH=${GCC_BIN}:$PATH
export CC=$GCC_BIN/gcc
export CPP=$GCC_BIN/cpp
export CXX=$GCC_BIN/g++
alias gcc=$CC
alias g++=$CXX
export LD_LIBRARY_PATH=${GCC_BASE}/lib64:${GCC_BASE}/lib:${LD_LIBRARY_PATH}

# Boost
BOOST_BASE=boost-1.55.0-python2.7-x86_64-slc6-gcc48
export BOOST_PATH=$ABASE/boost/$BOOST_BASE/$BOOST_BASE
export LD_LIBRARY_PATH=$BOOST_PATH/lib:${LD_LIBRARY_PATH}
export CPLUS_INCLUDE_PATH=$BOOST_PATH/include:${CPLUS_INCLUDE_PATH}

## root setup
export ROOTSYS=${ABASE}/root/6.04.14-x86_64-slc6-gcc49-opt
source $ROOTSYS/bin/thisroot.sh

# Pythia8
export PYTHIA8=/DFS-L/DATA/atlas/tfaucett/semi-visible-jets-ml/generation/gen/HEPTools/MG5/HEPTools/pythia8
DelphesPythia8=/DFS-L/DATA/atlas/tfaucett/semi-visible-jets-ml/generation/gen/HEPTools/MG5/Delphes/DelphesPythia8

# slurm settings
ncores=2
quiet=0
recurse=0
partition=atlas
#partition=atlas_all

show_help() {
    echo "Submit pythia/delphes jobs to the slurm cluster."
    echo "Usage: $0 [options] input_file [input_file ...]"
    echo "Options:"
    echo "  -t TAG_NAME     A prefix tag for output files (e.g. <TAG_NAME>_delphes.root)."
    echo "  -c N_CORES      Number of cores to request per job. (Default: $ncores)"
    echo "  -p PARTITION    The slurm partition to submit to. (Default: $partition)"
    echo "  -q              Squelch slurm logs."
}

# parse CLI
while getopts ":h?t:c:p:q" opt; do
    case "$opt" in
    h)  show_help
        exit 0
        ;;
    t)  tag=$OPTARG
        ;;
    c)  ncores=$OPTARG
        ;;
    p)  partition=$OPTARG
        ;;
    q)  quiet=1
        ;;
    \?)
        echo "Invalid option: -$OPTARG" >&2
    show_help
    exit 1
    ;;
    :)
        echo "Option: -$OPTARG requires argument." >&2
    show_help
    exit 1
    ;;
    esac
done
total_jobs=$1
rinv=$2

# setup options to sbatch command
SLURM_OPTS="-c $ncores -p $partition -t 1440"

if [ "$quiet" == "1" ]; then
	SLURM_OPTS+=" -o /dev/null"
fi

#madgraph gridpacks
run="0"

while [[ $run -lt $total_jobs ]]
do
    SLURM_OPTS+=" -o slurm-logs/rinv-$rinv-RUN-$run.log"
    sbatch $SLURM_OPTS ./python.sh $run $rinv
    run=$[$run+1]

done


