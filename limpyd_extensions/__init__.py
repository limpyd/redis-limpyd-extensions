"""Some extensions for redis-limpyd, a redis orm (sort of) in python"""

import pkg_resources
from future.builtins import str
from os import path
from setuptools.config import read_configuration


def _extract_version(package_name):
    try:
        # if package is installed
        version = pkg_resources.get_distribution(package_name).version
    except pkg_resources.DistributionNotFound:
        # if not installed, so we must be in source, with ``setup.cfg`` available
	    _conf = read_configuration(path.join(
	        path.dirname(__file__), '..', 'setup.cfg')
	    )
	    version = _conf['metadata']['version']

    return version


EXACT_VERSION = _extract_version('redis_limpyd_extensions')
VERSION = tuple(int(part) for part in EXACT_VERSION.split('.') if str(part).isnumeric())
