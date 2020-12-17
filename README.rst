DonJuan
=======

A translation/rebuild of the original `donjon dungeon generator <https://donjon.bin.sh/fantasy/dungeon/>`_.
This package aims to deconstruct the original script into extendable parts, and provide all pieces
for customization for different purposes and not just the map image. For example, when complete this package
will automatically generate walls, doors, and light sources for use in
`Foundry Virtual Tabletop <https://foundryvtt.com/>`_.

You can find the `documentation here <https://donjuan.readthedocs.io/en/latest/>`_.

Composability
-------------

Composability is a central design principle of this package. That is, complex
objects are composed of more simple ones. For example, a
`Dungeon` is composed of rooms and passages that are
fundamentally made up of `Cell` objects that individually have properties,
such as `Door` objects and `Faces`.


This is a work in progress.
