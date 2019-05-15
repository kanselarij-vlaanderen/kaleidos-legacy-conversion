#!/usr/bin/python3
import csv
from datetime import datetime

from .model.government import Government

DATASOURCE_REGERINGEN = '../../data/regeringen/vlaamse_regeringen.csv'

def create_governments():
    with open(DATASOURCE_REGERINGEN, 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';', quoting=csv.QUOTE_NONE)
        governments = []
        for row in reader:
            start, end = row['timerange'].split(' - ')
            installation_date = datetime.strptime(start.strip(), '%d %m %Y').date()
            if end.strip():
                resignation_date = datetime.strptime(end.strip(), '%d %m %Y').date()
            else:
                resignation_date = None
            governments.append(Government(row['regering'], installation_date, resignation_date))
        return governments
