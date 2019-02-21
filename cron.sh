#!/usr/bin/env sh
SCRIPTPATH=$(dirname $0)
cd $SCRIPTPATH

echo $(pwd)

localhome="--home=$(pwd)/localhome"

module_execute="-m karlsruher $localhome"

echo python3 $module_execute
python3 $module_execute $@
cd -
