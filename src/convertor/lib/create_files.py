#!/usr/bin/python3

import os.path

from .model.mu_file import MuFile

MIMETYPE_2_EXTENSION = {
    'application/msword': 'doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
    'application/pdf': 'pdf',
}

def create_file(file_src, physical_file_folder=None, metadata_lut=None, src2uuid_in=None, name=None):
    file = MuFile()
    file.physical_name = file_src['r_object_id']['parsed']
    if src2uuid_in and file.physical_name in src2uuid_in:
        file.uuid = src2uuid_in[file.physical_name]
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
    return file

def create_files(parsed_import, physical_file_folder=None, metadata_lut=None, src2uuid_in=None):
    files = []
    srcid2uuid_out = {}
    for file_src in parsed_import:
        file = create_file(file_src, physical_file_folder, metadata_lut, src2uuid_in)
        srcid2uuid_out[file.physical_name + '.' + file.extension] = file.uuid
        files.append(file)

    return files, srcid2uuid_out
