#!/usr/bin/python
# -*- coding: utf-8 -*-


import os
import sys

from easl import EASL


in_file_path = sys.argv[1]
dir_path = os.path.dirname(in_file_path)
file_name = os.path.splitext(os.path.basename(in_file_path))[0]
out_file_name = file_name + "_0" + os.extsep + "csv"
out_file_path = os.path.join(dir_path, out_file_name)

model = EASL()
model.initItem(in_file_path)
model.saveItem(out_file_path)
