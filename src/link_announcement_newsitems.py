#!/usr/bin/python3

import csv
import json
import sys

def load_governing_body_mapping(path):
    with open(path, mode='r') as f:
        uuids_by_ref = json.load(f)
    return uuids_by_ref


if __name__ == '__main__':

    AGENDAITEM_SRC = sys.argv[1]
    NEWS_ITEM_SRC = sys.argv[2]

    with open(AGENDAITEM_SRC, 'r') as f:
        ai_reader = csv.DictReader(f, fieldnames=['ai_src_uri', 'ni_src_uri'], delimiter=';')

        ai_by_ni_src = {}
        for row in ai_reader:
            # if row['ni_src_uri'] in ai_by_ni_src:
                # print("Non-unique key '{}'. Had '{}', now '{}'".format(row['ni_src_uri'], ai_by_ni_src[row['ni_src_uri']], row['ai_src_uri']))
            ai_by_ni_src[row['ni_src_uri']] = row['ai_src_uri']

    json_objs = 0
    with open(NEWS_ITEM_SRC, 'r') as f:
        ni_src_by_ni = {}
        for row in json.load(f)['results']['bindings']:
            json_objs += 1
            # if row['newsItem']['value'] in ni_src_by_ni:
                # print("Non-unique key '{}'. Had '{}', now '{}'".format(row['newsItem']['value'], ni_src_by_ni[row['newsItem']['value']], row['newsItemRef']['value']))
            ni_src_by_ni[row['newsItem']['value']] = row['newsItemRef']['value']

    hits = 0
    misses = 0
    for ni, ni_src in ni_src_by_ni.items():
        try:
            print("(<{}> <{}>)".format(ni_src, ai_by_ni_src[ni_src]))
            hits += 1
        except KeyError:
            # print("No match found for {}: {}".format(ni, ni_src))
            misses += 1
    # print("hits", hits, "misses", misses, "json_objs", json_objs)
