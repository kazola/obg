#!/usr/bin/bash
echo; echo; echo


# -----------------------------------------------------------------------
# curl -L https://raw.githubusercontent.com/LowellInstruments/fleak/master/installer/installer_fleak.sh | bash
# -----------------------------------------------------------------------


_e() {
  rv=$1
  if [ "$rv" -ne 0 ]; then
    printf '%s' "$2"
    exit 1
fi
}


printf '> CURL installer for Lowell Instruments FLEAK GUI console\n'
printf '> step 1) Creating virtual env\n'
rm -rf venv_fleak
python3 -m venv venv_fleak
source venv_fleak/bin/activate
_e $? 'error creating fleak virtual environment\n'


printf '> step 2) Installing MAT library'
git clone https://github.com/lowellinstruments/lowell-mat.git -b v4
cd lowell-mat && export MY_IGNORE_REQUIREMENTS_TXT=1 && pip install .
rm -rf lowell-mat
_e $? 'error installing MAT library\n'


printf '> step 3) Cloning repository fleak\n'
pip install git+https://github.com/lowellinstruments/fleak.git
_e $? 'error installing fleak\n'


printf '> done! now you type the following to run the fleak GUI\n'
printf 'source venv_fleak/bin/activate\n'
printf 'fleak\n'
