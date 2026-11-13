# pylint: disable=missing-docstring
from pathlib import Path
import re
from setuptools import setup

NAME = "hass-configurator"
PACKAGE_NAME = "hass_configurator"
# One authoritative value for both package metadata and runtime.
# Parse rather than import to avoid runtime dependencies during setup.
version_source = (Path(__file__).resolve().parent / PACKAGE_NAME / "_version.py").read_text(encoding="utf-8")
match = re.search(
    r'^VERSION = "([0-9]+\.[0-9]+\.[0-9]+(?:[a-zA-Z0-9.+-]*)?)"

setup(name=NAME,
      version=VERSION,
      description='HASS Configurator',
      long_description="https://github.com/danielperna84/hass-configurator",
      long_description_content_type='text/markdown',
      url='http://github.com/danielperna84/hass-configurator',
      project_urls={
          'Documentation': 'https://github.com/danielperna84/hass-configurator',
          'Tracker': 'https://github.com/danielperna84/hass-configurator/issues'
      },
      download_url='https://github.com/danielperna84/hass-configurator/tarball/'+VERSION,
      author='Daniel Perna',
      author_email='danielperna84@gmail.com',
      license='MIT',
      install_requires=['pyotp', 'gitpython', 'legacy-cgi'],  # legacy-cgi required for Python > 3.12
      packages=[PACKAGE_NAME],
      include_package_data=True,
      entry_points={
          'console_scripts': [
              'hass-configurator = hass_configurator.configurator:main'
          ]
      },
      keywords='home-assistant',
      platforms='any',
      python_requires='>=3',
      classifiers=[
          'Programming Language :: Python :: 3',
          'Operating System :: OS Independent',
          'Topic :: Text Editors'],
      zip_safe=False)
,
    version_source, re.MULTILINE,
)
if not match:
    raise RuntimeError("Missing or invalid VERSION in hass_configurator/_version.py")
VERSION = match.group(1)

setup(name=NAME,
      version=VERSION,
      description='HASS Configurator',
      long_description="https://github.com/danielperna84/hass-configurator",
      long_description_content_type='text/markdown',
      url='http://github.com/danielperna84/hass-configurator',
      project_urls={
          'Documentation': 'https://github.com/danielperna84/hass-configurator',
          'Tracker': 'https://github.com/danielperna84/hass-configurator/issues'
      },
      download_url='https://github.com/danielperna84/hass-configurator/tarball/'+VERSION,
      author='Daniel Perna',
      author_email='danielperna84@gmail.com',
      license='MIT',
      install_requires=['pyotp', 'gitpython', 'legacy-cgi'],  # legacy-cgi required for Python > 3.12
      packages=[PACKAGE_NAME],
      include_package_data=True,
      entry_points={
          'console_scripts': [
              'hass-configurator = hass_configurator.configurator:main'
          ]
      },
      keywords='home-assistant',
      platforms='any',
      python_requires='>=3',
      classifiers=[
          'Programming Language :: Python :: 3',
          'Operating System :: OS Independent',
          'Topic :: Text Editors'],
      zip_safe=False)
