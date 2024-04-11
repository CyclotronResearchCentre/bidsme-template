# Template notebooks for bidsification

This repository represents my standard setup for bidsification of a given dataset.
It is intended to be forked and adapted to each particular place.


## Folder structure

Template present several folders intended to organize bidsification-related files.
Using this organisation is absolutely not mandatory, but will require to adapt
notebooks.

### `map`

The `map` folder is expected to contain `bidsmap.yaml` bidsification map.
This file will be automatically created during map creation step.

### `plugin`

The `plugin` directory is expected to contain plugins files `prepare_plugin.py`
(for preparation step) and `bidsify_plugin.py` (for map and bidsification steps).

### `template`

The `template` directory is expected to contain `participants.json` sidecar JSON
file that used for generation of `participants.tsv` table.
You can place there the JSON files for other tables (e.g. for tasks tsv files).

### `notebook`

The `notebook` directory is expected to contain jupyter-lab notebooks, that runs
bidsification.


## Notebooks

The bidsification is performed using 4 notebooks, that are described below.
The notebooks are expected to run from within same virtual environment/kernel
(see the workflow below).

### `installation.ipynb`

The `installation.ipynb` notebook contains the commands for installing and
updating `bidsme` and other needed python packages.

> When running commands in this notebook, it is imperative to insure that
correct kernel is used. **Verify** outputs of first 3 cells of this notebook.

To install packages (for ex. `pandas`) using `pip`, you can create a cell
as follows:
```python
!{sys.executable} -m pip install pandas
```

Using `conda` as package manager, the syntax is different:
```python
!conda install --prefix {sys.prefix} pandas
```

> The `!{sys.executable}` is needed to install packages in current kernel
The `notebook` folder contains notebooks needed to bidsify a dataset:

Outside `bidsme`, this notebook contain the installation of `nbformat`
package, which need for interaction between notebooks.

Use this notebook only when needed to install/update packages.

You can install packages in the environment/kernel outside the notebook,
but doing it from within, will allow you to track what was installed.

### `configuration.ipynb`

The `configuration.ipynb` notebook contains the definitions of the paths
needed for bidsification.
For each defined path, a test for existence `assert os.path.isfile` or
`assert os.path.isdir` is defined.
It will be executed by other notebooks (to get defined paths), so it is
imperative that full `configuration.ipynb` runs without errors.

The function `generate_paths` in second cell, defines paths for dataset.
You need to adapt these paths to suit your workspace.
It provide paths for test and production datasets, based on parameter
`production` set to `True` or `False`.

Following definitions of paths are for plugins, maps and JSON templates.
If you will not use a given path(for ex. a plugin), do not hesitate to
comment or remove corresponding cells.


### `bidsification_dev.ipynb`

The `bidsification_dev.ipynb` perform bidsification of test dataset, and
includes `preparation`, `mapping` and `bidsification` steps.

Use this notebook for configure the bidsification, adjust options,
test plugins etc.

As for set-up, you are expected to run each of `bidsme` commands several
times, you are provided with cells that remove all files in `prepared`
and `bidsified` datasets.

The links in the notebook points to relevant plugin, map and templates,
and can be used for reference and quick edit, assuming that the names
are standard.


### `bidsification_prod.ipynb`

The `bidsification_prod.ipynb` perform bidsification of production dataset.
It is supposed to be run in it's full, each time new subjects are added to
the source dataset (Kernel -> RestartKernel and Run All Cells).
It contains only `preparation` and `bidsification` steps.

> Execute it only **after** `bidsification_dev.ipynb` runs without a hinge.

> It may happen that some subjects may produce unexpected errors. Copy such
subjects to the test dataset, and adjust map and/or plugins using
`bidsification_dev.ipynb`.

## Usage of virtual environments in jupyther-notebook/lab

> All commands must be executed in terminal.

To install and use notebooks in specific environment (named for ex. `bidsme`),
first this enveronment must be created:

[\*NIX](https://docs.python.org/3/tutorial/venv.html)
```
python3 -m venv bidsme_env -p python3.9
source bidsme_env/bin/activate
```

[Conda]
```
conda create --name bidsme_env python=3.9
conda activate bidsme_env
```

The optional parameters `-p python3.9` and `python=3.9` allow to specify
version of python to use.
It is nessesary for most modern systems, as `bidsme` is supports Python<3.11.

Once environment is activated, it must be registered as `ipython` kernel:
```
python -m pip install ipykernel
python -m ipykernel install --user --name bidsme --display-name "bidsme (Python 3.9)"
```

Then, the created kernell can be selected in the kernell drop-down list of notebooks.
