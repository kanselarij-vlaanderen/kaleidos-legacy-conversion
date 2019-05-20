#!/usr/bin/python3

import json
import os.path

import pymysql

from .model.news_item import Theme


dirname = os.path.dirname(__file__)
with open(os.path.join(dirname, './queries/themes.sql'), mode='r') as f:
    QUERY_THEMAS = f.read()

def create_themes(DB_CONFIG, uuid_lut=None):
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
        if uuid_lut:
            try:
                theme.uuid = uuid_lut[str(theme_src['id'])][0]
            except KeyError:
                theme.deprecated = True
        themes.append(theme)
    return themes

def themes_by_id(themes):
    return {theme.id: theme for theme in themes}


def load_theme_mapping(path):
    with open(path, mode='r') as f:
        uuids_by_id = json.load(f)
    return uuids_by_id
