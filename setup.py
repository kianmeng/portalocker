from __future__ import print_function

import os
import re
import sys
import typing
from distutils.version import LooseVersion

import setuptools
from setuptools import __version__ as setuptools_version
from setuptools.command.test import test as TestCommand

if LooseVersion(setuptools_version) < LooseVersion('38.3.0'):
    raise SystemExit(
        'Your `setuptools` version is old. '
        'Please upgrade setuptools by running `pip install -U setuptools` '
        'and try again.'
    )

# To prevent importing about and thereby breaking the coverage info we use this
# exec hack
about: typing.Dict[str, str] = {}
with open('portalocker/__about__.py') as fp:
    exec(fp.read(), about)

tests_require = [
    'pytest>=5.4.1',
    'pytest-cov>=2.8.1',
    'sphinx>=3.0.3',
    'pytest-flake8>=1.0.5',
    'pytest-mypy>=0.8.0',
    'redis',
]


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', 'Arguments to pass to pytest')]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ''

    def run_tests(self):
        import shlex
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


class Combine(setuptools.Command):
    description = 'Build single combined portalocker file'
    relative_import_re = re.compile(r'^from \. import (?P<name>.+)$',
                                    re.MULTILINE)
    user_options = [
        ('output-file=', 'o', 'Path to the combined output file'),
    ]

    def initialize_options(self):
        self.output_file = os.path.join(
            'dist', '%(package_name)s_%(version)s.py' % dict(
                package_name=about['__package_name__'],
                version=about['__version__'].replace('.', '-'),
            ))

    def finalize_options(self):
        pass

    def run(self):
        dirname = os.path.dirname(self.output_file)
        if dirname and not os.path.isdir(dirname):
            os.makedirs(dirname)

        output = open(self.output_file, 'w')
        print("'''", file=output)
        with open('README.rst') as fh:
            output.write(fh.read().rstrip())
            print('', file=output)
            print('', file=output)

        with open('LICENSE') as fh:
            output.write(fh.read().rstrip())

        print('', file=output)
        print("'''", file=output)

        names = set()
        lines = []
        for line in open('portalocker/__init__.py'):
            match = self.relative_import_re.match(line)
            if match:
                names.add(match.group('name'))
                with open('portalocker/%(name)s.py' % match.groupdict()) as fh:
                    line = fh.read()
                    line = self.relative_import_re.sub('', line)

            lines.append(line)

        import_attributes = re.compile(r'\b(%s)\.' % '|'.join(names))
        for line in lines[:]:
            line = import_attributes.sub('', line)
            output.write(line)

        print('Wrote combined file to %r' % self.output_file)


if __name__ == '__main__':
    setuptools.setup(
        name=about['__package_name__'],
        version=about['__version__'],
        description=about['__description__'],
        long_description=open('README.rst').read(),
        classifiers=[
            'Intended Audience :: Developers',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: Implementation :: CPython',
            'Programming Language :: Python :: Implementation :: PyPy',
        ],
        python_requires='>=3.5',
        keywords='locking, locks, with statement, windows, linux, unix',
        author=about['__author__'],
        author_email=about['__email__'],
        url=about['__url__'],
        license='PSF',
        package_data=dict(portalocker=['py.typed', 'msvcrt.pyi']),
        packages=setuptools.find_packages(exclude=[
            'examples', 'portalocker_tests']),
        # zip_safe=False,
        platforms=['any'],
        cmdclass={
            'combine': Combine,
            'test': PyTest,
        },
        install_requires=[
            # Due to CVE-2021-32559 updating the pywin32 requirement
            'pywin32>=226; platform_system == "Windows"',
        ],
        tests_require=tests_require,
        extras_require=dict(
            docs=[
                'sphinx>=1.7.1',
            ],
            tests=tests_require,
            redis=[
                'redis',
            ]
        ),
    )
