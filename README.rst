`Full Documentation <http://turf.readthedocs.org/en/latest/>`_

####
turf
####

**Configuration and environment inspection library**

Turf makes managing configuration for your Python application easy.
It provides a standard file access and naming convention,
as well as extensive configuration validation.
Turf allows you to specify what your applications configuration
should look like, and then worry about your application
and not parsing config files.

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


S3 Config Example IAM Policy
============================

.. code-block:: json

    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket",
                    "s3:PutObject"
                ],
                "Effect": "Allow",
                "Resource": [
                    "arn:aws:s3:::my-app-config",
                    "arn:aws:s3:::my-app-config/*"
                ],
                "Principal": {
                    "AWS": [
                        "arn:aws:iam:::role/my-app-role"
                    ]
                }
            }
        ]
    }