pyramid_frontend - Theme, Images, Assets Handling for Pyramid
=============================================================

.. image:: https://secure.travis-ci.org/storborg/pyramid_frontend.png
    :target: http://travis-ci.org/storborg/pyramid_frontend
.. image:: https://coveralls.io/repos/storborg/pyramid_frontend/badge.png?branch=master
    :target: https://coveralls.io/r/storborg/pyramid_frontend
.. image:: https://img.shields.io/pypi/v/pyramid_frontend.svg
    :target: https://crate.io/packages/pyramid_frontend
.. image:: https://img.shields.io/pypi/dm/pyramid_frontend.svg
    :target: https://crate.io/packages/pyramid_frontend

Scott Torborg - `Cart Logic <http://www.cartlogic.com>`_

Provides:

* Theme / template handling.
* Theme configuration.
* Theme stacking (one theme can inherit from another).
* Image filtering / serving.
* Asset handling and compilation.
* Uses Mako, PIL, require.js, and LESS.

Command line tools:

* Compile assets (in addition to a programmatic method for integrating with
  other build steps)

Extensive documentation is `hosted at Read the Docs <http://pyramid-frontend.readthedocs.org/en/latest/>`_.


Installation
============

Install with pip::

    $ pip install pyramid_frontend


License
=======

pyramid_frontend is licensed under an MIT license. Please see the LICENSE file
for more information.


Code Standards
==============

pyramid_frontend has a comprehensive test suite with 100% line and branch
coverage, as reported by the excellent ``coverage`` module. To run the tests,
simply run in the top level of the repo::

    $ nosetests

There are no `PEP8 <http://www.python.org/dev/peps/pep-0008/>`_ or
`Pyflakes <http://pypi.python.org/pypi/pyflakes>`_ warnings in the codebase. To
verify that::

    $ pip install pep8 pyflakes
    $ pep8 .
    $ pyflakes .

Any pull requests must maintain the sanctity of these three pillars.
