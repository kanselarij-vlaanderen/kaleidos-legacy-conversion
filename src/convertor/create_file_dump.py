#!/usr/bin/python3

import datetime
import logging
import os
import rdflib
import sys

import config
from load_file_metadata import load_file_metadata

from lib.util.import_helpers import import_csv
from lib.config.file_export_parsing_map import custom_trans_file
import lib.config.ttl_ns_repository as ns

from lib.create_files import create_files, load_file_mapping, dump_file_mapping

NOW = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

if __name__ == "__main__":

    file_metadata_lut = {}
    for file in [f for f in os.listdir(config.FILE_METADATA_FOLDER_PATH) if f.endswith('.csv')]:
        file_metadata_lut = {
            **file_metadata_lut,
            **load_file_metadata(os.path.join(config.FILE_METADATA_FOLDER_PATH, file))
        }
    file_uuid_lut = {}
    for file in [f for f in os.listdir(config.FILE_MAPPING_FOLDER_PATH) if f.endswith('.json')]:
        file_uuid_lut = {
            **file_uuid_lut,
            **load_file_mapping(os.path.join(config.FILE_MAPPING_FOLDER_PATH, file))
        }


    i = 0
    for context, files in config.EXPORT_FILES.items():
        for metadata_doc_type, path in files.items():
            i +=1
            parsed_file_source = import_csv(path, config.DORIS_EXPORT_ENCODING, custom_trans_file)

            export_folder_path = "exportDoris/{}/dar_doris_{}_{}/content/".format(context.upper(), context.lower(), metadata_doc_type)
            physical_file_folder = os.path.join(config.KALEIDOS_SHARE_EXPORT_SUBFOLDER, export_folder_path).rstrip('/') + '/'

            files, id2uuid_out = create_files(parsed_file_source, file_metadata_lut, physical_file_folder, file_uuid_lut)
            filename = '{}_{}_{}.json'.format(NOW, context, metadata_doc_type)
            dump_file_mapping(id2uuid_out, os.path.join(config.FILE_MAPPING_FOLDER_PATH, filename))

            g = rdflib.Graph(identifier=rdflib.URIRef(config.GRAPH_NAME))
            for file in files:
                if (context == 'VR') and (metadata_doc_type == 'document'):
                    file.folder_path += "{}/".format(str(file.physical_name[0:11]))
                for triple in file.triples(ns, config.KALEIDOS_API_URI):
                    g.add(triple)

            filename = 'kaleidos_file_{}_{}.ttl'.format(context, metadata_doc_type)
            g.serialize(format='turtle', destination=os.path.join(config.TTL_FOLDER_PATH, filename))

