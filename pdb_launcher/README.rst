==============
 Pdb Launcher
==============

Summary
=======

The purpose of this module is to provide an entrypoint for
`pdb <https://docs.python.org/3.5/library/pdb.html>`_ (or other) python debugger module.
It is useful when hard coding breakpoints is not an option. The list of saved
launcher setups is accessable from the technical menu. Debugger can be started by pressing a button
on the launcher form.

Breakpoints
===========

Breakpoints can be saved in sets for each specific launcher. They are written to the
rc file of the choosen debugger (i.e. ~/.pdbrc in case of pdb) right before the debugger launches.
Breakpoints can be defined by choosing an installed module and adding a relative file path and line number.
The method finds the installation path of the module and concatenates it to the file path.

Authors
=======

* János Gerzson (@grzs)
