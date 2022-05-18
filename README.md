# OPDx_read

OPDx_read is a small package that reads the proprietary file format OPDx, that is used by Dektak profilometers, and returns numpy arrays

## Installation

The installation is straightforward:

- clone the repository, by opening a command line and typing `git clone git@github.com:ThibaultCapelle/OPDx_read.git`

- enter the repository, by typing `cd OPDx_read`

- install the repository, by typing `python setup.py install`

## Basic use

To use it, just open a python console, and type for instance, to extract 1D datas:

```
from OPDx_read.reader import DektakLoad
loader=DektakLoad(filename)
x,y=loader.get_data_1D()
```

or for 2D datas:

```
from OPDx_read.reader import DektakLoad
loader=DektakLoad(filename)
x,y,z=loader.get_data_2D()
```

If you want to extract metadatas, you can call:

```
metadatas=loader.get_metadata()
```

which returns a dictionnary of all the metadatas.