# Recipes
---
`recipes.py` is  a (semi) convient way to store, edit, and print home cooking recipes.
It primarily relies on YAML files to store each recipe entry, resulting in a easily readable database.
On top of the YAML entries, a console interface (using Urwid) adds functionality to view, edit, and print.
The interface is built on top of a state machine to keep track of valid transitions between different views.
Currently, the print functionality relies on a networked FTP printer.
