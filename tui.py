git clone https://github.com/OxaC2000/cavactl.git
cd cavactl
python -m pytest          # nécessite : pip install pytest
pip install --user .
cavactl list
cavactl get general.bars
