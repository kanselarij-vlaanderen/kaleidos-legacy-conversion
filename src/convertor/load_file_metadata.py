#!/usr/bin/python3

import datetime

from lib.util.import_helpers import import_csv

custom_trans_meta = {
    'filename':  {'parser': str, 'required': True},
    'filesize': {'parser': int, 'required': False},
    'creation_date': {'parser': lambda d: datetime.datetime.fromisoformat(d.replace('Z', '+00:00')), 'required': False},
    'modified_date': {'parser': lambda d: datetime.datetime.fromisoformat(d.replace('Z', '+00:00')), 'required': False},
}

def load_file_metadata(path):
    metadata_lut = {}
    res = import_csv(path, custom_trans=custom_trans_meta)
    for line in res:
        metadata_lut_part = {}
        if line['filesize']['success'] and line['filesize']['parsed']:
            metadata_lut_part['filesize'] = line['filesize']['parsed']
        if line['filename']['success'] and line['filename']['parsed']:
            metadata_lut_part['filename'] = line['filename']['parsed']
        if line['creation_date']['success'] and line['creation_date']['parsed']:
            metadata_lut_part['creation_date'] = line['creation_date']['parsed']
        if line['modified_date']['success'] and line['modified_date']['parsed']:
            metadata_lut_part['modified_date'] = line['modified_date']['parsed']
        metadata_lut[line['filename']['parsed']] = metadata_lut_part
    return metadata_lut
