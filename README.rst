.. |BUILD STATUS| image:: https://github.com/tmcclintock/donjuan/workflows/Build%20Status/badge.svg?branch=main
	    :target: https://github.com/tmcclintock/donjuan/actions
.. |COVERALLS| image:: https://coveralls.io/repos/github/tmcclintock/donjuan/badge.svg?branch=main
	       :target: https://coveralls.io/github/tmcclintock/donjuan?branch=main

.. |LICENSE| image:: https://img.shields.io/badge/License-CC0%201.0-lightgrey.svg
	     :target: http://creativecommons.org/publicdomain/zero/1.0/

|BUILD STATUS| |COVERALLS| |LICENSE|

DonJuan
=======

A translation/rebuild of the original `donjon dungeon generator
<https://donjon.bin.sh/fantasy/dungeon/>`_.
This package aims to deconstruct the original script into extendable parts,
and provide all pieces for customization for different purposes and not just
the map image. For example, when complete this package will automatically
generate walls, doors, and light sources for use in
`Foundry Virtual Tabletop <https://foundryvtt.com/>`_.

You can find the `documentation here
<https://donjuan.readthedocs.io/en/latest/>`_.

GUI Application
---------------

A desktop GUI ships alongside the library. To launch it::

    python run_gui.py

**Generate panel** — configure grid size, render style, room parameters, door
probability, and seed, then press *Generate*. Use *Regenerate* (``Cmd+R``) to
replay the last seed.

**Texture packs** — four built-in packs (Stone, Cave, Wood, Sandstone) each
with toggleable wall shadows, torchlight, moss & cracks, pillars, and wall
outlines.

**Edit mode** (``Cmd+Shift+E`` or the *Edit* button) — switches the left panel
to an edit-focused view and enables direct manipulation of the dungeon:

* **Click / drag** — paint cells filled (wall) or open (floor).
* **Shift + click** — toggle a door on the nearest wall edge.
* **Alt + click** — stamp the selected *Room Theme* onto the clicked room or
  hallway.
* **Cmd + Z** — undo (up to 20 steps).

**Room Themes** — six floor-colour presets (Default, Treasury, Throne, Prison,
Barracks, Crypt) that can be applied to individual rooms or hallways in edit
mode.

**FoundryVTT export** — exports the dungeon as a scene bundle (background image
+ JSON) ready for import into `Foundry Virtual Tabletop
<https://foundryvtt.com/>`_. Hovering over the *Export* button previews the
wall, door, and light placement as an overlay on the canvas.

Installation
------------

Install ``donjuan`` with ``pip``:

.. code-block:: bash

   pip install donjuan

You can find the package details `here on PyPI
<https://pypi.org/project/donjuan/>`_.

You can also install ``donjuan`` using the ``setup.py`` file. To do so, you must
first clone or download this repository and install the requirements.

Assuming you have `git <https://git-scm.com/>`_, you can do:

.. code-block:: bash

   git clone https://github.com/tmcclintock/donjuan
   cd donjuan
   pip install -r requirements.txt

Then you can install with:

.. code-block:: bash

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

which can be done from the root of the repository. To run all tests, including
those with graphical outputs, run with the ``runslow`` flag:

.. code-block:: bash

   pytest --runslow

Please report any issues you encounter on our `issue page
<https://github.com/tmcclintock/donjuan/issues>`_. Doing so will help make
``donjuan`` even better!

Contributing
------------

To contribute to ``donjuan`` please see the `developing page
<https://donjuan.readthedocs.io/en/latest/developing.html>`_.
