.. |TRAVIS| image:: https://travis-ci.com/tmcclintock/donjuan.svg?branch=main
	    :target: https://travis-ci.com/github/tmcclintock/donjuan
.. |COVERALLS| image:: https://coveralls.io/repos/github/tmcclintock/donjuan/badge.svg?branch=main
	       :target: https://coveralls.io/github/tmcclintock/donjuan?branch=main

.. |LICENSE| image:: https://img.shields.io/badge/License-CC0%201.0-lightgrey.svg
	     :target: http://creativecommons.org/publicdomain/zero/1.0/

|TRAVIS| |COVERALLS| |LICENSE|

DonJuan
=======

**HACKATHON** - a list of todo items for the 12/20/20 Hackathon can be found
on the issues page!

A translation/rebuild of the original `donjon dungeon generator <https://donjon.bin.sh/fantasy/dungeon/>`_.
This package aims to deconstruct the original script into extendable parts, and provide all pieces
for customization for different purposes and not just the map image. For example, when complete this package
will automatically generate walls, doors, and light sources for use in
`Foundry Virtual Tabletop <https://foundryvtt.com/>`_.

You can find the `documentation here <https://donjuan.readthedocs.io/en/latest/>`_.

Installation
------------

Installing `donjuan` is possible using the `setup.py` file. When the package is
more mature, we will cut a release on PyPI. For now, the steps to install are
to clone or download this repository and install into your Python environment.

Assuming you have `git <https://git-scm.com/>`_, you can do:

.. code-block:: bash

   git clone https://github.com/tmcclintock/donjuan
   cd donjuan
   pip install -r requirements.txt
   python setup.py install

If you have `conda
<https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_ you can install the requirements using the `environment.yml` file
before installing:

.. code-block:: bash

   conda env create -f environment.yml
   conda activate donjuan
   python setup.py install

To run the test suite, you must have `pytest
<https://docs.pytest.org/en/stable/>`_ installed. You can run the tests with:

.. code-block:: bash

   pytest

which can be done from the root of the repository.

Note that the only requirement at the moment is `pillow
<https://pillow.readthedocs.io/en/stable/>`_.

Contributing
------------

To contribute to `donjuan` please see the `developing <https://donjuan.readthedocs.io/en/latest/developing.html>`_ page.
