#!/usr/bin/bash
echo; echo; echo


# -----------------------------------------------------------------------
# curl https://raw.githubusercontent.com/LowellInstruments/fleak/master/settings/installer_fleak.sh | bash
# -----------------------------------------------------------------------


printf '> CURL installer for Lowell Instruments FLEAK GUI console\n'
printf '> step 1) Creating virtual env'
rm -rf venv_fleak
python -m venv venv_fleak
. venv_fleak/bin/activate
rv=$?
if [ "$rv" -ne 0 ]; then
    printf 'error creating fleak virtual environment'
    exit 1
fi


printf '> step 2) Cloning repository fleak'
pip install git+https://github.com/lowellinstruments/fleak.git
rv=$?
if [ "$rv" -ne 0 ]; then
    printf 'error installing fleak'
    exit 1
fi
