#!/usr/bin/bash

# ----------------------------------------------------
# curl -L <online_location_of_this_sh_file.sh> | bash
# ----------------------------------------------------

_e() {
  rv=$1
  if [ "$rv" -ne 0 ]; then printf '%s' "$2"; exit 1; fi
}

echo; echo; echo
printf '=== CURL installer for Lowell Instruments BLE GUI console, aka fleak === \n'


printf '\n\n> step 1) Creating virtual env\n'
    rm -rf venv_fleak; python3 -m venv venv_fleak; source venv_fleak/bin/activate
    _e $? 'error creating fleak virtual environment\n'


printf '\n\n> step 2) Cloning MAT library\n'
    rm -rf lowell-mat || true
    git clone https://github.com/lowellinstruments/lowell-mat.git -b v4
    _e $? 'error cloning MAT library\n'


printf '\n\n> step 3) Installing MAT library\n'
    cp lowell-mat/tools/_setup_wo_reqs.py lowell-mat/setup.py
    pip3 install ./lowell-mat
    _e $? 'error installing MAT library\n'


printf '\n\n> step 4) Installing fleak\n'
    pip install git+https://github.com/lowellinstruments/fleak.git
_   e $? 'error installing fleak\n'


printf '\n\n> done! now you type the following to run the fleak GUI\n\n'
printf '$ source venv_fleak/bin/activate\n'
printf '$ fleak\n'
