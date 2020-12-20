.. |TRAVIS| image:: https://travis-ci.com/tmcclintock/donjuan.svg?branch=main
	    :target: https://travis-ci.com/github/tmcclintock/donjuan
.. |COVERALLS| image:: https://coveralls.io/repos/github/tmcclintock/donjuan/badge.svg?branch=main
	       :target: https://coveralls.io/github/tmcclintock/donjuan?branch=main

Welcome to donjuan's documentation!
===================================

|TRAVIS| |COVERALLS| |LICENSE|

This package is a rebuild of the `donjon <https://donjon.bin.sh/code/dungeon/>`_
dungeon generator, with all the benefits that come from using modern tools.
In `donjuan`, all parts of the dungeon are objects that can be subclassed
and serialized (saved to disk) on their own. This includes things like walls,
doors, and rooms, as well as algorithms for actual dungeon generation,
renderers for different image formats, and exporters for saving map files for
different VTT applications.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   readme
   developing


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
