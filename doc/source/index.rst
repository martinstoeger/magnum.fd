.. Magneto documentation master file, created by
   sphinx-quickstart on Sat Feb 12 19:20:58 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: /figures/logo.svg

Welcome to magnum.fd's documentation!
=====================================
magnum.fd is a finite-difference/FFT package for the solution of dynamical micromagnetic problems. It is written in Python, C++ and Cuda C and runs on CPU as well as GPU.

Original Project MicroMagnum
++++++++++++++++++++++++++++
magnum.fd is forked from MicroMagnum (https://github.com/MicroMagnum/MicroMagnum) that was developed by the MicroMagnum Team:

* Andre Drews (Head of Team)
* Gunnar Selke (Lead Developer)
* Benjamin Krueger
  - Accurate (and fast!) calculation of the demagnetization tensor, with support for periodic boundary conditions.
  - Oersted field module (in development)
* Claas Abert
  - Calculation of the demagnetization field from its scalar potential.
* Theo Gerhardt
  - Geometrical shapes for the simulation description.

Download
++++++++
Visit our `GitHub page <https://github.com/micromagnetics/magnum.fd>`_ to download magnum.fd.

License and Disclaimer
++++++++++++++++++++++
magnum.fd is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Alternatives
++++++++++++
You might also want to have a look at these open-source finite-difference micromagnetic codes:

* mumax (http://mumax.github.io/)
* OOMMF (http://math.nist.gov/oommf/)

You code is not listed here, but should be? Drop us a line (claas.abert@tuwien.ac.at).

.. toctree::
   :maxdepth: 2

   install
   gettingstarted
   world
   solver
   controller
   toolboxes
   modules
   io
   cmdargs
   models
   license

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

