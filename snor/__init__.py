# -*- coding: utf-8 -*-
import os

# Create db and tables if it doesn't exist
if not os.path.exists('database.db'):
    open('database.db', 'a').close()
    from models import *
    Show.create_table()
    Episode.create_table()

from server import *