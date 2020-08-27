#!/bin/sh

(cd apluslms_roman_qt && pyrcc5 -o roman_rc.py roman.qrc)

python3 -m apluslms_roman_qt.gui
