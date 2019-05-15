#!/usr/bin/python3
import itertools
import logging
import os.path

import html2text
import pymysql
from pytz import timezone

from .config.nieuwsberichten import DB_CONFIG
from .model.news_item import NewsItem

TIMEZONE = timezone('Europe/Brussels')
dirname = os.path.dirname(__file__)
with open(os.path.join(dirname, './queries/agenda_items.sql'), mode='r') as f:
    QUERY_AGENDAPUNTEN = f.read()

def create_news_item_from_src(src):
    try:
        if src['agenda_date'] and src['body_value'] and (src['body_format'] in ('geen_tabellen', 'filtered_html')):
            structured_text = src['body_value']
            plain_text = html2text.html2text(src['body_value'])
            ni = NewsItem(src['nid'], src['agenda_date'], src['description'], plain_text, structured_text)
            ni.public = bool(int(src['status']))
            if src['date_published']:
                ni.date_published = TIMEZONE.localize(src['date_published'])
            if src['documents_date_published']:
                ni.documents_date_published = TIMEZONE.localize(src['documents_date_published'])
        else:
            raise ValueError("'{}' isn't a valid date for news-item ({}, {})".format(src['agenda_date'], src['nid'], src['description']))
        item_nr_like = int(src['agenda_item_nr'])
        if item_nr_like > 900:
            ni.agenda_item_nr = item_nr_like - 900
            ni.agenda_item_type = 'MEDEDELING'
        elif item_nr_like > 0:
            ni.agenda_item_nr = item_nr_like
            ni.agenda_item_type = 'PUNT'
        else:
            raise ValueError("'{}' isn't a valid agenda item number ({}, {})".format(src['agenda_item_nr'], ni.id, ni.title))
    except Exception as e:
        raise ValueError("Failed parsing news item source data '{}'\n{}".format(src, e))

    ni.theme_refs = list(set(map(int, src['policy_area_ids'].split(',')))) if src['policy_area_ids'] else [] # Conversion to set for uniqueness
    ni.mandatee_refs = list(set(map(int, src['minister_ids'].split(',')))) if src['minister_ids'] else []
    ni.document_refs = list(set(src['document_ids'].split(','))) if src['document_ids'] else []
    return ni

def create_news_items():
    connection = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    try:
        with connection.cursor() as cursor:
            news_items = []
            # Read a single record
            cursor.execute(QUERY_AGENDAPUNTEN)
            while True:
                news_item_src = cursor.fetchone()
                if news_item_src:
                    try:
                        news_item = create_news_item_from_src(news_item_src)
                    except ValueError as e:
                        logging.warning('Failed to parse news item {}, {}'.format(news_item_src, e))
                        continue
                    news_items.append(news_item)
                else:
                    break
    finally:
        connection.close()
    logging.info('Found {} news items.'.format(len(news_items)))
    return news_items

def group_news_items_by_agenda_date(news_items):
    news_items_by_agenda_date = {}
    for k, g in itertools.groupby(news_items, lambda ni: ni.agenda_date):
        l = [e for e in g]
        l.sort(key=lambda ni: (ni.agenda_item_type, ni.agenda_item_nr))
        news_items_by_agenda_date[k] = tuple(l)
    return news_items_by_agenda_date
