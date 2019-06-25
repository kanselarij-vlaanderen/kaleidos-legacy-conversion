#!/usr/bin/python3

import logging
import os
import rdflib

import config
from lib.util.import_helpers import import_csv
from lib.config.oc_export_parsing_map import custom_trans_document, custom_trans_fiche
import lib.config.ttl_ns_repository as ns
from lib.model.document_version import DocumentVersion
from lib.model.document import Document
from lib.model.document_name import DocumentName, OcDocumentName, OcAgendaName, OcNotulenName
from lib.document_version_creator import create_files_document_versions_agenda_items, group_doc_vers_by_source_name, group_doc_vers_by_parsed_name, group_doc_vers_by_object_id

from lib.create_agendas import create_agendas
from lib.search import find_agenda_document, find_notulen_document, find_agenda

from lib.create_news_items import create_news_items, group_news_items_by_agenda_date
# from import_nieuwsberichten.role_creator import create_roles, roles_by_label
from lib.create_themes import create_themes, themes_by_id, load_theme_mapping
from lib.create_files import load_file_mapping

from lib.create_document_types import create_document_types
from lib.create_dossiers import create_dossiers
from lib.create_administrations import create_administrations
from lib.create_submitters import load_governing_body_mapping, governing_body_uri
from load_file_metadata import load_file_metadata

###########################################################
# PARSE AND LOAD METADATA
###########################################################
file_metadata_lut = {}
# for file in [f for f in os.listdir(config.FILE_METADATA_FOLDER_PATH) if f.endswith('.csv') and 'errata' not in f]:
#     file_metadata_lut = {
#         **file_metadata_lut,
#         **load_file_metadata(os.path.join(config.FILE_METADATA_FOLDER_PATH, file))
#     }
file_uuid_lut = {}
# for file in [f for f in os.listdir(config.FILE_MAPPING_FOLDER_PATH) if f.endswith('.json')]:
#     file_uuid_lut = {
#         **file_uuid_lut,
#         **load_file_mapping(os.path.join(config.FILE_MAPPING_FOLDER_PATH, file))
#     }

parsed_doc_source = import_csv(config.EXPORT_FILES['OC']['document'],
                               config.DORIS_EXPORT_ENCODING,
                               custom_trans_document)
parsed_fiche_source = import_csv(config.EXPORT_FILES['OC']['fiche'],
                                 config.DORIS_EXPORT_ENCODING,
                                 custom_trans_fiche)

theme_uuid_lut = load_theme_mapping(config.THEME_MAPPING_FILE_PATH)

governing_body_uuid_lut = load_governing_body_mapping(config.SUBMITTER_MAPPING_FILE_PATH)

###########################################################
# CONVERT TO OBJECT MODEL
###########################################################
doc_parsed = create_files_document_versions_agenda_items(parsed_doc_source, file_metadata_lut, file_uuid_lut)
fiche_parsed = create_files_document_versions_agenda_items(parsed_fiche_source, file_metadata_lut, file_uuid_lut)
files = doc_parsed[0] + fiche_parsed[0]
document_versions = doc_parsed[1] + fiche_parsed[1]
agenda_items = doc_parsed[2] + fiche_parsed[2]
parsed_doc_vers = list(filter(lambda d: isinstance(d.parsed_name, OcDocumentName), document_versions))
agenda_doc_vers = list(filter(lambda d: isinstance(d.parsed_name, OcAgendaName), parsed_doc_vers))
notulen_doc_vers = list(filter(lambda d: isinstance(d.parsed_name, OcNotulenName), document_versions))
ordinary_doc_vers = list(filter(lambda d: isinstance(d.parsed_name, OcDocumentName), parsed_doc_vers))
# fiche_doc_vers = list(filter(lambda d: isinstance(d.parsed_name, VrBeslissingsficheName), parsed_doc_vers))
unparsed_doc_vers = list(filter(lambda d: d.parsed_name is None, document_versions))


agendas = create_agendas(agenda_items)

doc_types_by_label = create_document_types()


###########################################################
# LINK REFERENCES
###########################################################
documents_by_stuknummer = group_doc_vers_by_source_name(document_versions)
doc_vers_by_stuknummer_parsed = group_doc_vers_by_parsed_name(agenda_doc_vers + notulen_doc_vers + ordinary_doc_vers)

documents_by_name = {}

for document_version in document_versions:
    if document_version.parsed_name and isinstance(document_version.parsed_name, DocumentName):
        name = document_version.parsed_name.name()
    else:
        name = document_version.source_name
    if document_version.version:
        version = document_version.version
    else:
        version = 1
    try:
        document = documents_by_name[name]
        if version in document.document_versions.keys():
            logging.warning("Already a version '{}' in the versions collection of document '{}' ... skipping".format(version, name))
        else:
            document.document_versions[version] = document_version
    except KeyError:
        document = Document(document_version)
        documents_by_name[name] = document
    document_version.link_document_refs(documents_by_stuknummer, doc_vers_by_stuknummer_parsed)
    document_version.link_type_refs(doc_types_by_label)

# roles_by_label = roles_by_label(roles)


i = 0
found_rel_docs, total_rel_docs = 0, 0
for agenda in agendas:
    agenda.link_agenda_doc(agenda_doc_vers)
    agenda.link_notulen_doc(notulen_doc_vers)
    for ap in agenda.agendapunten:
        # Link documents + stats
        ap.link_document_refs(documents_by_stuknummer, doc_vers_by_stuknummer_parsed)
        if ap._document_refs:
            if agenda.datum and (agenda.datum > config.BEGINDATUM_DORIS_REFERENTIES):
                total_rel_docs += len(ap._document_refs)
                found_rel_docs += len(ap.rel_docs)
    print(agenda)

logging.info("Found {} out of {} documents ({:.1f}%) referenced in {} agendapoints".format(found_rel_docs, total_rel_docs, found_rel_docs/total_rel_docs*100, i))


dossiers_by_year_dossiernr = create_dossiers(agendas) # Requires agendapunt.rel_docs to be linked

administrations = create_administrations()

submitters_lut, persons = create_submitters_by_ref(agendas, administrations, submitter_uuid_lut)
import pdb; pdb.set_trace()
for s in submitters_lut.values():
    print(s)
import pdb; pdb.set_trace()

for agenda in agendas:
    for ap in agenda.agendapunten:
        ap.beslissingsfiche.link_indiener_refs(submitters_lut, administrations)
        for rel_doc in ap.rel_docs:
            ap.beslissingsfiche.link_indiener_refs(submitters_lut, administrations)


if __name__ == "__main__":
    g = rdflib.Graph(identifier=rdflib.URIRef(config.GRAPH_NAME))

    for doc_ver in document_versions:
        for triple in doc_ver.triples(ns, config.KALEIDOS_API_URI, config.DORIS_EXPORT_URI):
            g.add(triple)

    for doc in documents_by_name.values():
        for triple in doc.triples(ns, config.KALEIDOS_API_URI):
            g.add(triple)

    for agenda in agendas:
        for triple in agenda.triples(ns, config.KALEIDOS_API_URI):
            g.add(triple)
        for ap in agenda.punten:
            for triple in ap.triples(ns, config.KALEIDOS_API_URI, config.DORIS_EXPORT_URI):
                g.add(triple)

    for dossier in dossiers_by_year_dossiernr.values():
        for triple in dossier.triples(ns, config.KALEIDOS_API_URI):
            g.add(triple)

    filename = 'kaleidos_oc.ttl'
    g.serialize(format='turtle', destination=os.path.join(config.TTL_FOLDER_PATH, filename))
