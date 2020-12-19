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
