#!/bin/bash
set -e

if [[ $0 == $${BASH_SOURCE[0]} ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

function finish {
  cd $owd
}
owd=$(pwd)
trap finish EXIT

cd $(dirname ${BASH_SOURCE[0]})/..
root_dir=$(pwd)

if [[ ! -d venv ]] ; then
   mkdir venv
fi

PYTHON=${PYTHON:-python}
$PYTHON -m venv venv
. venv/bin/activate
PIP=${PIP:-pip}
${PIP} install -e .
cd Mathics
$PYTHON ./setup.py develop
