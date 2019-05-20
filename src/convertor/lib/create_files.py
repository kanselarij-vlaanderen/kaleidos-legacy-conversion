#!/usr/bin/python3

import json

from .model.mu_file import MuFile

MIMETYPE_2_EXTENSION = {
    'application/msword': 'doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/pdf': 'pdf',
}

def create_file(file_src, metadata_lut=None, physical_file_folder=None, uuid_lut=None):
    file = MuFile()
    file.physical_name = file_src['r_object_id']['parsed']
    file.mimetype = file_src['a_content_type']['parsed'][1]
    file.name = file_src['object_name']['source']
    try:
        file.extension = MIMETYPE_2_EXTENSION[file.mimetype]
    except KeyError:
        raise ValueError('Unknown mimetype \'{}\''.format(file.mimetype))
    if physical_file_folder:
        file.folder_path = physical_file_folder
    if metadata_lut:
        try:
            f = metadata_lut[file.physical_name + '.' + file.extension]
            if 'filesize' in f:
                file.size = f['filesize']
            if 'creation_date' in f:
                file.created = f['creation_date']
        except KeyError:
            pass
    if uuid_lut:
        try:
            file.uuid = uuid_lut[file.physical_name + '.' + file.extension]
        except KeyError:
            pass
    return file

def create_files(parsed_import, metadata_lut=None, physical_file_folder=None, uuid_lut=None):
    files = []
    uuid_lut_out = {}
    for file_src in parsed_import:
        file = create_file(file_src, metadata_lut, physical_file_folder, uuid_lut)
        uuid_lut_out[file.physical_name + '.' + file.extension] = file.uuid
        files.append(file)

    return files, uuid_lut_out

def load_file_mapping(path):
    with open(path, mode='r') as f:
        uuids_by_id = json.load(f)
    return uuids_by_id

def dump_file_mapping(uuid_lut, path):
    with open(path, mode='w') as f:
        json.dump(uuid_lut, f)
