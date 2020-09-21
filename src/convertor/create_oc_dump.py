#!/usr/bin/python3

import itertools
import logging
import os
import rdflib

import config
from lib.util.rreplace import rreplace
from lib.util.import_helpers import import_csv
from lib.config.oc_export_parsing_map import custom_trans_document, custom_trans_fiche
import lib.config.ttl_ns_repository as ns
from lib.model.oc import Session, AgendaItem, Case
from lib.model.document_name import DocumentName, OcDocumentName, OcAgendaName, OcNotulenName, OcNotificatieName

from lib.create_submitters import load_governing_body_mapping, governing_body_uri
from lib.create_files import create_file, load_file_mapping

from lib.doris_export_parsers import p_oc_fed_case_name

from load_file_metadata import load_file_metadata

from lib.oc_document_version_creator import create_files_document_versions_agenda_items, group_doc_vers_by_source_name
from lib.create_oc_documents import create_documents
from lib.create_oc_agendas import create_agendas

###########################################################
# PARSE AND LOAD METADATA
###########################################################
file_metadata_lut = {}
for file in [f for f in os.listdir(config.FILE_METADATA_FOLDER_PATH) if f.endswith('.csv') and 'errata' not in f]:
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

parsed_doc_source = import_csv(config.EXPORT_FILES['OC']['document'],
                               config.DORIS_EXPORT_METADATA_ENCODING,
                               custom_trans_document)
parsed_fiche_source = import_csv(config.EXPORT_FILES['OC']['fiche'],
                                 config.DORIS_EXPORT_METADATA_ENCODING,
                                 custom_trans_fiche)

governing_body_uuid_lut = load_governing_body_mapping(config.SUBMITTER_MAPPING_FILE_PATH)

###########################################################

doc_parsed = create_files_document_versions_agenda_items(parsed_doc_source, config.DORIS_EXPORT_URI, file_metadata_lut, file_uuid_lut)
fiche_parsed = create_files_document_versions_agenda_items(parsed_fiche_source, config.DORIS_EXPORT_URI, file_metadata_lut, file_uuid_lut)
files = doc_parsed[0] + fiche_parsed[0]
document_versions = doc_parsed[1] + fiche_parsed[1]

doc_vers_by_source_name = group_doc_vers_by_source_name(document_versions)

documents = create_documents(document_versions)

sessions = create_agendas(document_versions)

cases_by_id = {}

total_rel_docs, found_rel_docs = 0, 0
for session in sessions:
    for item in session.agenda_items:
        # Set correct submiter references
        if item.notification and item.notification._indiener_refs:
            for ind in item.notification._indiener_refs:
                try:
                    uri = governing_body_uri(config.KALEIDOS_API_URI, governing_body_uuid_lut[ind])
                    item.submitter_uris.append(uri)
                except KeyError:
                    pass
        # Link cases (and create them if needed)
        if item.subject:
            try:
                case_ref = next(filter(lambda c: not c[1], p_oc_fed_case_name(item.subject)))
                case_id, in_parens = case_ref
                try:
                    item.case = cases_by_id[case_id]
                except KeyError:
                    cases_by_id[case_id] = Case(case_id)
                    item.case = cases_by_id[case_id]
                if item.subject.endswith(case_id):
                    item.subject = rreplace(item.subject, case_id, '', 1).rstrip(' \n')
            except StopIteration:
                pass

        # Link documents + stats
        item.link_document_refs(doc_vers_by_source_name)
        if item.notification and item.notification._decision_doc_refs:
            total_rel_docs += len(item.notification._decision_doc_refs)
            found_rel_docs += len(item.notification_documents)


if __name__ == "__main__":
    g = rdflib.Graph(identifier=rdflib.URIRef(config.GRAPH_NAME))

    for doc_ver in document_versions:
        for triple in doc_ver.triples(ns, config.KALEIDOS_API_URI):
            g.add(triple)

    for doc in documents:
        for triple in doc.triples(ns, config.KALEIDOS_API_URI):
            g.add(triple)

    for session in sessions:
        # print(session)
        for triple in session.triples(ns, config.KALEIDOS_API_URI):
            g.add(triple)
        for item in session.agenda_items:
            for triple in item.triples(ns, config.KALEIDOS_API_URI):
                g.add(triple)
        # print('\n')
    for case in cases_by_id.values():
        for triple in case.triples(ns, config.KALEIDOS_API_URI):
            g.add(triple)

    filename = 'kaleidos-oc-sensitive.ttl'
    g.serialize(format='turtle', destination=os.path.join(config.TTL_FOLDER_PATH, filename))
