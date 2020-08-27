#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from codecs import open
from datetime import datetime
from os import path
from setuptools import setup, find_packages
from sys import argv, platform, version_info as pyver
from shutil import rmtree

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

py2app = 'py2app' in argv

options = dict(
    name='apluslms-roman-qt',
    version='0.1.0',
    description='Course material builder for online learning systems (Qt gui)',
    long_description=long_description,
    keywords='apluslms material',
    url='https://github.com/apluslms/roman-qt',
    author='Jaakko Kantojärvi',
    author_email='jaakko.kantojarvi@aalto.fi',
    license='GPLv3',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',
    ],

    zip_safe=True,
    packages=['apluslms_roman_qt'],
    include_package_data = True,
    package_data={
        '': ['*.json'],
    },

    install_requires=[
        'apluslms-roman >= 0.1.0',
    ],

    entry_points={
        'console_scripts': [
            'roman-qt = apluslms_roman_qt.gui:main',
        ],
    },
)


if platform == 'darwin':
    APP_NAME = 'Roman'
    options.update(dict(
        app=['gui.py'],
    ))
    options.setdefault('options', {})['py2app'] = {
        'bdist_base': 'build',
        'dist_dir': 'dist',
        'force_system_tk': True,
        'iconfile': 'packaging/osx/roman.icns',
        'plist': {
            'CFBundleName': APP_NAME,
            'CFBundleDisplayName': APP_NAME,
            'CFBundleGetInfoString': options['description'],
            'CFBundleIdentifier': "io.github.apluslms.RomanQt",
            'CFBundleVersion': "1.0",
            'CFBundleShortVersionString': options['version'],
            'NSHumanReadableCopyright': u"Copyright © {}, {}".format(
                datetime.now().year,
                options['author'],
            ),
        },
    }
    options.setdefault('setup_requires', []).extend([
        'py2app >= 0.12, != 0.14',
    ])

if __name__ == '__main__':
    setup(**options)

    # remove unneeded paths from the app
    if py2app:
        remove = []
        qt_dir = path.join(options['options']['py2app']['dist_dir'],
            "{}.app".format(APP_NAME), 'Contents', 'Resources', 'lib',
            'python{}.{}'.format(pyver[0], pyver[1]), 'PyQt5', 'Qt')
        lib_dir = path.join(qt_dir, 'lib')
        remove += [path.join(lib_dir, x) for x in [
            'QtBluetooth.framework',
            'QtConcurrent.framework',
            #'QtCore.framework',
            'QtDBus.framework',
            'QtDesigner.framework',
            #'QtGui.framework',
            'QtHelp.framework',
            'QtLocation.framework',
            'QtMacExtras.framework',
            'QtMultimedia.framework',
            'QtMultimediaWidgets.framework',
            'QtNetwork.framework',
            'QtNetworkAuth.framework',
            'QtNfc.framework',
            'QtOpenGL.framework',
            'QtPositioning.framework',
            #'QtPrintSupport.framework', # base requirement
            'QtQml.framework',
            'QtQuick.framework',
            'QtQuickControls2.framework',
            'QtQuickParticles.framework',
            'QtQuickTemplates2.framework',
            'QtQuickTest.framework',
            'QtQuickWidgets.framework',
            'QtSensors.framework',
            'QtSerialPort.framework',
            'QtSql.framework',
            'QtSvg.framework',
            'QtTest.framework',
            'QtWebChannel.framework',
            'QtWebEngine.framework',
            'QtWebEngineCore.framework',
            'QtWebEngineWidgets.framework',
            'QtWebSockets.framework',
            #'QtWidgets.framework',
            'QtXml.framework',
            'QtXmlPatterns.framework',
        ]]
        plugin_dir = path.join(qt_dir, 'plugins')
        remove += [path.join(plugin_dir, x) for x in [
            'audio',
            'bearer',
            'gamepads',
            'generic',
            'geometryloaders',
            'geoservices',
            'iconengines',
            'imageformats',
            'mediaservice',
            #'platforms',  # base requirement
            'playlistformats',
            'position',
            'printsupport',
            'renderplugins',
            'sceneparsers',
            'sensorgestures',
            'sensors',
            'sqldrivers',
            #'styles',  # base requirement
            'texttospeech',
        ]]

        for dir_ in remove:
            if path.isdir(dir_):
                print("removed: ", dir_)
                rmtree(dir_)
