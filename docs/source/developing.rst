.. _developing Contributing:

Developing
==========

Developing `donjuan` should follow best practices. This includes documentation,
testing, and using composability.

Composability is the design concept that complex objects use more simple
objects that are responsible for very specfic tasks. For example, a
`Dungeon` is composed of rooms and passages that are fundamentally made up
of `Cell` objects that individually have properties, such as `Door` objects
and `Faces`.

If you want to implement a new piece of logic and you are not sure where it
goes, create a new class for it and use that class as appropriate.

Contributing
------------

To contribute, please start by forking the repository and creating a branch
for the feature you would like to work on. Once you clone your feature branch,
install the developer environment, activate it and install `donjuan` in
editable mode:

.. code-block:: bash

   conda env create -f environment_dev.yml
   conda activate djdev
   pip install -e .

In this setup, any changes you make to the source code of `donjuan` will be
seen immediately by your `djdev` environment. Furthermore, you will not have
to reinstall `donjuan` if you switch branches.

Once your development environment is activated, please install `pre-commit
<https://pre-commit.com/>`_ before committing any changes:

.. code-block:: bash

   pre-commit install

This way, any time you perform a `git commit` command, the `black`, `flake8`,
and `isort` packages will run to clean up your code. If you see a "failure"
message, then simply `git reset` and then fix any issues the `pre-commit`
packages are giving you. If `pre-commit` is being too annoying, then you can
always recreate your conda environment without installing it.

Once your code is ready, commit and push it to your branch and issue a Pull
Request on GitHub.

Testing data and a sample dungeon
---------------------------------

Tests should be written in the `tests/` directory, so that running `pytest` at
the root finds and runds all tests found there. Tests should be functions
attached to classes that subclass `unittest.TestCase`. This allows you to write
`setUp` and `tearDown` functions that run before and after all tests.
A sample dungeon is found in `tests/fixtures/dummy_dungeon.json`, where the
`filled` attribute of a five-by-five dungeon have been saved in a 2D array.
To load in this dungeon in memory simply run:

.. code-block:: python

   import json
   fp ="/path/tp/dummy_dungeon.json"
   with open(fp, "r") as file:
       dungeon_json = json.load(file)
   dungeon_array = dungeon_json["dungeon"]  # the actual array

Then, to turn this into an actual `Dungeon` object, instantiate a `Dungeon`
that is five by five and assign the `filled` values according to the values
in the read array.

.. code-block:: python

   dungeon = Dungeon(n_rows=5, n_cols=5)

   for i in range(5):
       for j in range(5):
           dungeon.grid.cells[i][j].filled = bool(dungeon_array[i][j])
