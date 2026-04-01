.. |BUILD STATUS| image:: https://github.com/tmcclintock/donjuan/workflows/Build%20Status/badge.svg?branch=main
	    :target: https://github.com/tmcclintock/donjuan/actions
.. |COVERALLS| image:: https://coveralls.io/repos/github/tmcclintock/donjuan/badge.svg?branch=main
	       :target: https://coveralls.io/github/tmcclintock/donjuan?branch=main

.. |LICENSE| image:: https://img.shields.io/badge/License-CC0%201.0-lightgrey.svg
	     :target: http://creativecommons.org/publicdomain/zero/1.0/

|BUILD STATUS| |COVERALLS| |LICENSE|

DonJuan
=======

DonJuan is a procedural battle-map generator for tabletop RPG scenes. It began
as a rebuild of the original `donjon dungeon generator
<https://donjon.bin.sh/fantasy/dungeon/>`_, and has since grown into a modular
scene-generation toolkit with a desktop GUI, multiple renderers, and
FoundryVTT export.

Current scene types include:

- **Dungeon** — rooms, hallways, doors, textured dungeon rendering
- **Forest** — trees, undergrowth, outdoor forest rendering
- **Camp** — tents, campfires, paths, perimeter trees
- **Village** — enterable buildings, roads, and scattered trees

You can find the `documentation here
<https://donjuan.readthedocs.io/en/latest/>`_.

Package layout
--------------

The library is organized by reusable core primitives plus scene-specific
packages:

- ``donjuan/core`` — shared grid/cell/space primitives, common Foundry export
  base classes, reusable `Room` / `Hallway`, and shared room size/position
  randomizers
- ``donjuan/dungeon`` — dungeon-specific generation, rendering, and export
- ``donjuan/forest`` — forest-specific generation, rendering, and export
- ``donjuan/camp`` — camp-specific generation, rendering, and export
- ``donjuan/village`` — village-specific generation, rendering, and export

GUI Application
---------------

A desktop GUI ships alongside the library. To launch it::

    python run_gui.py

The generate panel now supports all four scene types. Depending on the scene,
the controls expose room/building sizing, road/corridor parameters, tree or
undergrowth density, camp layout controls, texture-pack selection, and seed
replay.

**Generate panel** — configure scene parameters and press *Generate*. Use
*Regenerate* (``Cmd+R``) to replay the last seed.

**Texture packs** — dungeon rendering includes four built-in packs (Stone,
Cave, Wood, Sandstone) with toggleable wall shadows, torchlight, moss &
cracks, pillars, and wall outlines.

**Edit mode** (``Cmd+Shift+E`` or the *Edit* button) — currently supported for
dungeon scenes only:

* **Click / drag** — paint cells filled (wall) or open (floor)
* **Shift + click** — toggle a door on the nearest wall edge
* **Alt + click** — stamp the selected room theme onto the clicked room or
  hallway
* **Cmd + Z** — undo (up to 20 steps)

**Room Themes** — six floor-colour presets (Default, Treasury, Throne, Prison,
Barracks, Crypt) can be applied to dungeon rooms and hallways in edit mode.

**FoundryVTT export** — dungeon, forest, camp, and village scenes can all be
exported as a scene bundle (background image + JSON) ready for import into
`Foundry Virtual Tabletop <https://foundryvtt.com/>`_. Hovering over the
*Export* button previews exported walls, doors, and lights on the canvas.

Installation
------------

Install ``donjuan`` with ``pip``:

.. code-block:: bash

   pip install donjuan

You can find the package details `here on PyPI
<https://pypi.org/project/donjuan/>`_.

You can also install ``donjuan`` using the ``setup.py`` file. To do so, you
must first clone or download this repository and install the requirements.

Assuming you have `git <https://git-scm.com/>`_, you can do:

.. code-block:: bash

   git clone https://github.com/tmcclintock/donjuan
   cd donjuan
   pip install -r requirements.txt

Then you can install with:

.. code-block:: bash

   python setup.py install

If you have `conda
<https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_
you can install the requirements using the ``environment.yml`` file before
installing:

.. code-block:: bash

   conda env create -f environment.yml
   conda activate donjuan
   python setup.py install

Testing
-------

To run the test suite, you must have `pytest
<https://docs.pytest.org/en/stable/>`_ installed. You can run the fast suite
with:

.. code-block:: bash

   python3 -m pytest tests/ -m "not slow"

To run all tests, including graphical/image-writing tests:

.. code-block:: bash

   python3 -m pytest tests/ --runslow

Please report any issues you encounter on our `issue page
<https://github.com/tmcclintock/donjuan/issues>`_. Doing so will help make
``donjuan`` even better.

Contributing
------------

To contribute to ``donjuan`` please see the `developing page
<https://donjuan.readthedocs.io/en/latest/developing.html>`_.
