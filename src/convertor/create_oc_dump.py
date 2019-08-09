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

all_source = parsed_doc_source + parsed_fiche_source

sessions = []
files = []
cases_by_id = {}

def by_session(doc_src):
    return doc_src['dar_date_vergadering']['parsed']

def by_item(doc_src):
    return doc_src['dar_volgnummer']['parsed']

def is_agenda(doc_src):
    return (doc_src['object_name']['success'] and isinstance(doc_src['object_name']['parsed'], OcAgendaName)) or \
        (doc_src['dar_aard']['source'] == 'Agenda')

def is_meeting_record(doc_src):
    return doc_src['object_name']['success'] and isinstance(doc_src['object_name']['parsed'], OcNotulenName)
    
def is_notification(doc_src):
    return doc_src['object_name']['success'] and isinstance(doc_src['object_name']['parsed'], OcNotificatieName)

valid_doc_versions = list(filter(lambda d: d['dar_date_vergadering']['success'], all_source))
valid_doc_versions = sorted(valid_doc_versions, key=by_session)
docs_per_session = itertools.groupby(valid_doc_versions, by_session)
for session_date, docs_1 in docs_per_session:
    docs_1 = list(docs_1)
    session = Session(session_date)
    sessions.append(session)
    try:
        file = create_file(next(filter(is_agenda, docs_1)), file_metadata_lut, None, file_uuid_lut)
        files.append(file)
        session.agenda = file
    except (TypeError, StopIteration):
        logging.warning("Didn't find agenda doc for session {}".format(session.started_at))
    try:
        file = create_file(next(filter(is_meeting_record, docs_1)), file_metadata_lut, None, file_uuid_lut)
        files.append(file)
        session.meeting_record = file
    except (TypeError, StopIteration):
        logging.warning("Didn't find meeting record (notulen) doc for session {}".format(session.started_at))
    # import pdb; pdb.set_trace()
    # Group by agenda item
    valid_item_docs = list(filter(lambda src: src['dar_volgnummer']['success'], docs_1))
    valid_item_docs = sorted(valid_item_docs, key=by_item)
    docs_per_agenda_item = itertools.groupby(valid_item_docs, by_item)
    for priorities, docs_2 in docs_per_agenda_item:
        priority, sub_priority = priorities
        docs_2 = list(docs_2)
        if priority > 0: # Regular items
            item = AgendaItem(priority, docs_2[0]['dar_onderwerp']['parsed'], sub_priority)
            session.agenda_items.append(item)
            try:
                src = next(filter(is_notification, docs_2))
                file = create_file(src, file_metadata_lut, None, file_uuid_lut)
                files.append(file)
                item.notification = file
                item.subject = src['dar_onderwerp']['parsed']
                if src['dar_indiener_samenvatting']['success']:
                    for ind in src['dar_indiener_samenvatting']['parsed']:
                        try:
                            uri = governing_body_uri(config.KALEIDOS_API_URI, governing_body_uuid_lut[ind])
                            item.submitter_uris.append(uri)
                        except KeyError:
                            pass
                try:
                    case_ref = next(filter(lambda c: not c[1], p_oc_fed_case_name(src['dar_onderwerp']['source'])))
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
            except (TypeError, StopIteration):
                logging.warning("Didn't find notification doc for agenda {} item {}{}".format(session.started_at, priority, sub_priority))
                src = None
            for doc in docs_2:
                if not doc == src:
                    file = create_file(doc, file_metadata_lut, None, file_uuid_lut)
                    files.append(file)
                    item.documents.append(file)
# Sort sessions by date
sessions.sort(key=lambda s: session.started_at)


if __name__ == "__main__":
    g = rdflib.Graph(identifier=rdflib.URIRef(config.GRAPH_NAME))

    for session in sessions:
        print(session)
        for triple in session.triples(ns, config.KALEIDOS_API_URI):
            g.add(triple)
        for item in session.agenda_items:
            print(item)
            for triple in item.triples(ns, config.KALEIDOS_API_URI):
                g.add(triple)
        print('\n')
    for case in cases_by_id.values():
        for triple in case.triples(ns, config.KALEIDOS_API_URI):
            g.add(triple)

    filename = 'kaleidos-oc-sensitive.ttl'
    g.serialize(format='turtle', destination=os.path.join(config.TTL_FOLDER_PATH, filename))
