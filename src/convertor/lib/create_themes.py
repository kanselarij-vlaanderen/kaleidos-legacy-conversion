#!/usr/bin/python3
import os.path

import pymysql

from .config.nieuwsberichten import DB_CONFIG
from .model.news_item import Theme

dirname = os.path.dirname(__file__)
with open(os.path.join(dirname, './queries/themes.sql'), mode='r') as f:
    QUERY_THEMAS = f.read()

def create_themes():
    connection = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    try:
        with connection.cursor() as cursor:
            # Read a single record
            cursor.execute(QUERY_THEMAS)
            themas_src = cursor.fetchall()
    finally:
        connection.close()

    themes = []
    for theme_src in themas_src:
        theme = Theme(theme_src['name'])
        theme.id = theme_src['id']
        themes.append(theme)
    return themes

def themes_by_id(themes):
    return {theme.id: theme for theme in themes}
