`Full Documentation <http://turf.readthedocs.org/en/latest/>`_

####
turf
####

**Configuration and environment inspection library**

Get Turf
========

.. code-block:: shell
    pip install turf

Run the tests
=============

.. code-block:: shell

    git clone git@github.com:HurricaneLabs/turf.git
    cd turf
    tox

Examples
--------

Basic Configuration Manager
===========================

.. code-block:: shell
    $ cat /tmp/turftest/foo.yml 
    ---
    blah: bar

.. code-block:: python
    from turf.config import BaseConfig

    class MyConfig(BaseConfig):
        config_dir = "/tmp/turftest"
        schema = {"foo":{"blah":{"type":"string"}}}

    print(MyConfig.section("foo")["blah"])

Will produce::
    bar







