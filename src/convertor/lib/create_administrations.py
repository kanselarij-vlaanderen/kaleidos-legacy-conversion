#!/usr/bin/python3
import csv
from datetime import datetime

from .model.governing_body import GoverningBody

DATASOURCE_REGERINGEN = '../../data/regeringen/vlaamse_regeringen.csv'

def create_administrations():
    """ Load bestuursorganen in de tijd """
    with open(DATASOURCE_REGERINGEN, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';', quoting=csv.QUOTE_NONE)
        governments = []
        for row in reader:
            start, end = row['timerange'].split(' - ')
            installation_date = datetime.strptime(start.strip(), '%d %m %Y').date()
            resignation_date = datetime.strptime(end.strip(), '%d %m %Y').date() if end.strip() else None
            gov = GoverningBody(row['regering'], installation_date, resignation_date)
            gov.uuid = row['uuid'].strip()
            gov.minister_mandate_uri = row['minister_mandate_uri'].strip()
            governments.append(gov)
        return governments
