#!/usr/bin/python3

import logging
import os
import pymysql
import rdflib

import config
from lib.util.import_helpers import import_csv
from lib.config.vr_export_parsing_map import custom_trans_document, custom_trans_fiche
import lib.config.ttl_ns_repository as ns
from lib.model.document_version import DocumentVersion
from lib.model.document import Document
from lib.model.document_name import DocumentName, AgendaName, VrBeslissingsficheName, VrDocumentName, VrNotulenName
from lib.document_version_creator import create_files_document_versions_agenda_items, group_doc_vers_by_source_name, group_doc_vers_by_parsed_name, group_doc_vers_by_object_id

from lib.create_agendas import create_agendas
from lib.create_submitters import load_submitter_mapping, create_submitters_by_ref
from lib.search import find_agenda_document, find_notulen_document, find_agenda

from lib.create_news_items import create_news_items, group_news_items_by_agenda_date
# from import_nieuwsberichten.role_creator import create_roles, roles_by_label
from lib.create_themes import create_themes, themes_by_id, load_theme_mapping
from lib.create_files import load_file_mapping

from lib.create_dossiers import create_dossiers
from lib.create_administrations import create_administrations
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

parsed_doc_source = import_csv(config.EXPORT_FILES['VR']['document'],
                               config.DORIS_EXPORT_ENCODING,
                               custom_trans_document)
parsed_fiche_source = import_csv(config.EXPORT_FILES['VR']['fiche'],
                                 config.DORIS_EXPORT_ENCODING,
                                 custom_trans_fiche)

theme_uuid_lut = load_theme_mapping(config.THEME_MAPPING_FILE_PATH)

submitter_uuid_lut = load_submitter_mapping(config.SUBMITTER_MAPPING_FILE_PATH)

###########################################################
# CONVERT TO OBJECT MODEL
###########################################################
doc_parsed = create_files_document_versions_agenda_items(parsed_doc_source, config.DORIS_EXPORT_URI, file_metadata_lut, file_uuid_lut)
fiche_parsed = create_files_document_versions_agenda_items(parsed_fiche_source, config.DORIS_EXPORT_URI, file_metadata_lut, file_uuid_lut)
files = doc_parsed[0] + fiche_parsed[0]
document_versions = doc_parsed[1] + fiche_parsed[1]
agenda_items = doc_parsed[2] + fiche_parsed[2]
parsed_doc_vers = list(filter(lambda d: isinstance(d.parsed_name, DocumentName), document_versions))
agenda_doc_vers = list(filter(lambda d: isinstance(d.parsed_name, AgendaName), parsed_doc_vers))
notulen_doc_vers = list(filter(lambda d: isinstance(d.parsed_name, VrNotulenName), document_versions))
ordinary_doc_vers = list(filter(lambda d: isinstance(d.parsed_name, VrDocumentName), parsed_doc_vers))
fiche_doc_vers = list(filter(lambda d: isinstance(d.parsed_name, VrBeslissingsficheName), parsed_doc_vers))
unparsed_doc_vers = list(filter(lambda d: d.parsed_name is None, document_versions))


agendas = create_agendas(agenda_items)

connection = pymysql.connect(**config.NIEUWSBERICHTEN_DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
news_items = create_news_items(connection, config.NIEUWSBERICHTEN_EXPORT_URI)

themes = create_themes(config.NIEUWSBERICHTEN_DB_CONFIG, config.NIEUWSBERICHTEN_EXPORT_URI, theme_uuid_lut)


###########################################################
# LINK REFERENCES
###########################################################
documents_by_stuknummer = group_doc_vers_by_source_name(document_versions)
doc_vers_by_stuknummer_parsed = group_doc_vers_by_parsed_name(agenda_doc_vers + notulen_doc_vers + ordinary_doc_vers)

documents_by_name = {}

for document_version in document_versions:
    if document_version.parsed_name:
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
    document_version.document = document
    document_version.link_document_refs(documents_by_stuknummer, doc_vers_by_stuknummer_parsed)

# roles_by_label = roles_by_label(roles)

theme_lut = themes_by_id(themes)
doc_vers_by_object_id = group_doc_vers_by_object_id(document_versions)
for news_item in news_items:
    news_item.link_theme_refs(theme_lut, lambda id: id)
    news_item.link_document_refs(doc_vers_by_object_id, lambda id: id)
    # news_item.link_mandatee_refs(mandatees_by_src_id, lambda id: id)

i = 0
found_rel_docs, total_rel_docs = 0, 0
found_nis, expected_nis = 0, 22136
news_items_by_agenda_date = group_news_items_by_agenda_date(news_items)
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

        # Link news items + stats
        if agenda.datum >= config.BEGINDATUM_NIEUWSBERICHTEN:
            ni = ap.link_news_item(news_items_by_agenda_date)
            if ni:
                found_nis += 1

logging.info("Found {} out of {} documents ({:.1f}%) referenced in {} agendapoints".format(found_rel_docs, total_rel_docs, found_rel_docs/total_rel_docs*100, i))
logging.info("Found {} out of {} expected news items ({:.1f}%) for {} agendapoints".format(found_nis, expected_nis, found_nis/expected_nis*100, i))

dossiers_by_year_dossiernr = create_dossiers(agendas) # Requires agendapunt.rel_docs to be linked

administrations = create_administrations()

submitters_lut, persons = create_submitters_by_ref(agendas, administrations, submitter_uuid_lut)

for agenda in agendas:
    for ap in agenda.agendapunten:
        # Link subcases
        ap.link_subcase_refs(dossiers_by_year_dossiernr, config.KALEIDOS_API_URI) # Needs dossiers
        ap.beslissingsfiche.link_indiener_refs(submitters_lut, administrations)
        for rel_doc in ap.rel_docs:
            ap.beslissingsfiche.link_indiener_refs(submitters_lut, administrations)


if __name__ == "__main__":
    g = rdflib.Graph(identifier=rdflib.URIRef(config.GRAPH_NAME))

    for doc_ver in document_versions:
        for triple in doc_ver.triples(ns, config.KALEIDOS_API_URI):
            g.add(triple)

    for doc in documents_by_name.values():
        for triple in doc.triples(ns, config.KALEIDOS_API_URI):
            g.add(triple)

    for agenda in agendas:
        for triple in agenda.triples(ns, config.KALEIDOS_API_URI):
            g.add(triple)
        for ap in agenda.punten:
            for triple in ap.triples(ns, config.KALEIDOS_API_URI):
                g.add(triple)

    for dossier in dossiers_by_year_dossiernr.values():
        for triple in dossier.triples(ns, config.KALEIDOS_API_URI):
            g.add(triple)

    for news_item in news_items:
        for triple in news_item.triples(ns, config.KALEIDOS_API_URI):
            g.add(triple)

    for theme in filter(lambda t: t.deprecated, themes): # Code list for themes exists. Only dump deprecated (odd, unknown) ones.
        for triple in theme.triples(ns, config.KALEIDOS_API_URI):
            g.add(triple)

    for person in persons:
        for triple in person.triples(ns, config.KALEIDOS_API_URI):
            g.add(triple)

    for submitter in filter(lambda s: s.deprecated, submitters_lut.values()):  # Code list for government body submitters exists. Only dump deprecated (odd, unknown) ones.
        for triple in submitter.triples(ns, config.KALEIDOS_API_URI):
            g.add(triple)

    filename = 'kaleidos_vr.ttl'
    g.serialize(format='turtle', destination=os.path.join(config.TTL_FOLDER_PATH, filename))
