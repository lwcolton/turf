from setuptools import setup, find_packages
from codecs import open
import os

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "version"), "r") as version_handle:
    version = version_handle.read().strip()

long_description = """
`Github <https://github.com/HurricaneLabs/turf>`_
------------------------------------------------------
`Documentation <http://turf.readthedocs.org/en/latest>`_
-------------------------------------------------------------
"""

setup(
	name = "turf",
	version = version,
	description = "A python configuration library",
    long_description = long_description,
	url = "https://github.com/HurricaneLabs/turf",
	author = "Colton Leekley-Winslow",
	author_email = "colton@hurricanelabs.com",
	package_dir = {"":"src"},
	packages = find_packages("src"),
    install_requires = ["pyyaml"],
)

