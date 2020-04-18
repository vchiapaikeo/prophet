# Copyright (c) Facebook, Inc. and its affiliates.

# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os.path
import platform
import sys
import os
from pkg_resources import (
    normalize_path,
    working_set,
    add_activation_listener,
    require,
)
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop
from setuptools.command.test import test as test_command
from typing import List

PLATFORM = 'unix'
if platform.platform().startswith('Win'):
    PLATFORM = 'win'

MODEL_DIR = os.path.join('stan', PLATFORM)
MODEL_TARGET_DIR = os.path.join('fbprophet', 'stan_model')


def get_backends_from_env() -> List[str]:
    from fbprophet.models import StanBackendEnum
    return os.environ.get("STAN_BACKEND", StanBackendEnum.PYSTAN.name).split(",")


def build_models(target_dir):
    from fbprophet.models import StanBackendEnum
    for backend in get_backends_from_env():
        StanBackendEnum.get_backend_class(backend).build_model(target_dir, MODEL_DIR)


class BuildPyCommand(build_py):
    """Custom build command to pre-compile Stan models."""

    def run(self):
        if not self.dry_run:
            target_dir = os.path.join(self.build_lib, MODEL_TARGET_DIR)
            self.mkpath(target_dir)
            build_models(target_dir)

        build_py.run(self)


class DevelopCommand(develop):
    """Custom develop command to pre-compile Stan models in-place."""

    def run(self):
        if not self.dry_run:
            target_dir = os.path.join(self.setup_path, MODEL_TARGET_DIR)
            self.mkpath(target_dir)
            build_models(target_dir)

        develop.run(self)


class TestCommand(test_command):
    user_options = [
        ('test-module=', 'm', "Run 'test_suite' in specified module"),
        ('test-suite=', 's',
         "Run single test, case or suite (e.g. 'module.test_suite')"),
        ('test-runner=', 'r', "Test runner to use"),
        ('test-slow', 'w', "Test slow suites (default off)"),
    ]

    def initialize_options(self):
        super(TestCommand, self).initialize_options()
        self.test_slow = False

    def finalize_options(self):
        super(TestCommand, self).finalize_options()
        if self.test_slow is None:
            self.test_slow = getattr(self.distribution, 'test_slow', False)

    """We must run tests on the build directory, not source."""

    def with_project_on_sys_path(self, func):
        # Ensure metadata is up-to-date
        self.reinitialize_command('build_py', inplace=0)
        self.run_command('build_py')
        bpy_cmd = self.get_finalized_command("build_py")
        build_path = normalize_path(bpy_cmd.build_lib)

        # Build extensions
        self.reinitialize_command('egg_info', egg_base=build_path)
        self.run_command('egg_info')

        self.reinitialize_command('build_ext', inplace=0)
        self.run_command('build_ext')

        ei_cmd = self.get_finalized_command("egg_info")

        old_path = sys.path[:]
        old_modules = sys.modules.copy()

        try:
            sys.path.insert(0, normalize_path(ei_cmd.egg_base))
            working_set.__init__()
            add_activation_listener(lambda dist: dist.activate())
            require('%s==%s' % (ei_cmd.egg_name, ei_cmd.egg_version))
            func()
        finally:
            sys.path[:] = old_path
            sys.modules.clear()
            sys.modules.update(old_modules)
            working_set.__init__()


with open('requirements.txt', 'r') as f:
    install_requires = f.read().splitlines()

setup(
    name='fbprophet',
    version='0.6.1.dev0',
    description='Automatic Forecasting Procedure',
    url='https://facebook.github.io/prophet/',
    author='Sean J. Taylor <sjtz@pm.me>, Ben Letham <bletham@fb.com>',
    author_email='sjtz@pm.me',
    license='MIT',
    packages=find_packages(),
    setup_requires=[
        # "attrs==19.3.0",
        # "cachetools==3.1.1",
        # "certifi==2020.4.5.1",
        # "chardet==3.0.4",
        # "cmdstanpy==0.9.5",
        "convertdate==2.2.0",
        # "cycler==0.10.0",
        # "ephem==3.7.7.1",
        # "fbprophet==0.6.1.dev0",
        "holidays==0.10.2",
        # "httplib2==0.17.2",
        # "idna==2.8",
        # "importlib-metadata==1.6.0",
        # "kiwisolver==1.2.0",
        "korean-lunar-calendar==0.2.1",
        "LunarCalendar==0.0.9",
        # "marshmallow==2.13.6",
        # "matplotlib==3.2.1",
        # "mock==4.0.2",
        # "more-itertools==8.2.0",
        "numpy==1.18.2",
        # "packaging==20.3",
        "pandas==1.0.3",
        "plotly==4.6.0",
        # "pluggy==0.13.1",
        # "protobuf==3.11.3",
        # "py==1.8.1",
        # "pyasn1==0.4.8",
        # "pyasn1-modules==0.2.8",
        # "PyMeeus==0.3.7",
        # "PyMySQL==0.9.3",
        # "pyparsing==2.4.7",
        # "pystan==2.18.0.0",
        # "pytest==5.4.1",
        # "python-dateutil==2.8.1",
        # "python-json-logger==0.1.11",
        # "pytz==2019.3",
        # "requests==2.22.0",
        # "retrying==1.3.3",
        # "rsa==4.0",
        # "setuptools-git==1.2",
        # "six==1.14.0",
        # "SQLAlchemy==1.3.12",
        "tqdm==4.45.0",
        # "uritemplate==3.0.1",
        # "urllib3==1.25.9",
        # "wcwidth==0.1.9",
        # "zipp==3.1.0",
    ],
    install_requires=install_requires,
    zip_safe=False,
    include_package_data=True,
    cmdclass={
        'build_py': BuildPyCommand,
        'develop': DevelopCommand,
        'test': TestCommand,
    },
    test_suite='fbprophet.tests',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    long_description="""
Implements a procedure for forecasting time series data based on an additive model where non-linear trends are fit with yearly, weekly, and daily seasonality, plus holiday effects. It works best with time series that have strong seasonal effects and several seasons of historical data. Prophet is robust to missing data and shifts in the trend, and typically handles outliers well.
"""
)
