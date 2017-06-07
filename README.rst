========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |requires|
        | |coveralls| |codecov|
        | |codacy|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|

.. |docs| image:: https://readthedocs.org/projects/bluepea/badge/?style=flat
    :target: https://readthedocs.org/projects/bluepea
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/smithsamuelm/bluepea.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/smithsamuelm/bluepea

.. |requires| image:: https://requires.io/github/smithsamuelm/bluepea/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/smithsamuelm/bluepea/requirements/?branch=master

.. |coveralls| image:: https://coveralls.io/repos/smithsamuelm/bluepea/badge.svg?branch=master&service=github
    :alt: Coverage Status
    :target: https://coveralls.io/r/smithsamuelm/bluepea

.. |codecov| image:: https://codecov.io/github/smithsamuelm/bluepea/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/smithsamuelm/bluepea

.. |codacy| image:: https://img.shields.io/codacy/REPLACE_WITH_PROJECT_ID.svg
    :target: https://www.codacy.com/app/smithsamuelm/bluepea
    :alt: Codacy Code Quality Status

.. |version| image:: https://img.shields.io/pypi/v/bluepea.svg
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/bluepea

.. |commits-since| image:: https://img.shields.io/github/commits-since/smithsamuelm/bluepea/v0.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/smithsamuelm/bluepea/compare/v0.1.0...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/bluepea.svg
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/bluepea

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/bluepea.svg
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/bluepea

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/bluepea.svg
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/bluepea


.. end-badges

Indigo Project Backend

* Free software: Apache2 license

Installation
============

::

    pip install bluepea

Documentation
=============

https://bluepea.readthedocs.io/

Development
===========

To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
