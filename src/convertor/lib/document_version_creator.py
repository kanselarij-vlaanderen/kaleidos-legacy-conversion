#!/usr/bin/python3
import itertools
import logging

from .doris_export_parsers import p_doc_name, p_oc_doc_name
from .model.document_version import DocumentVersion
from .model.document_name import VrBeslissingsficheName, OcBeslissingsficheName, VersionedDocumentName
from .model.agenda import Agendapunt
from .create_files import create_file

def title_from_dar_onderwerp(dar_onderwerp):
    try:
        lines = dar_onderwerp.splitlines()
    except AttributeError:
        return None
    n_lines = len(lines)
    if lines[-1] == '':
        n_lines -= 1
    if n_lines > 1 and not lines[0].startswith(('-', 'A.', 'A ', 'A)')):
        return lines[0].strip()
    return None

def description_from_dar_onderwerp(dar_onderwerp):
    try:
        lines = dar_onderwerp.splitlines()
    except AttributeError:
        return None
    n_lines = len(lines)
    if lines[-1] == '':
        n_lines -= 1
    if n_lines > 1:
        if lines[0].startswith(('-', 'A.', 'A ', 'A)')):
            return '\n'.join(lines).rstrip()
        else:
            return '\n'.join(lines[1:]).rstrip()
    elif n_lines == 1:
        return lines[0].strip()
    return None

def create_files_document_versions_agenda_items(parsed_import, file_metadata_lut, file_uuid_lut=None):
    files = []
    documenten = []
    agendapunten = []
    for doc_src in parsed_import:
        if 'dar_fiche_type' in doc_src:
            doc_src_type = 'fiche'
        elif 'dar_doc_type' in doc_src:
            doc_src_type = 'document'
        else:
            raise Exception("Document type should be 'fiche' or 'document'")

        file = create_file(doc_src, file_metadata_lut, None, file_uuid_lut)
        files.append(file)
        doc = DocumentVersion(doc_src['r_object_id']['parsed'], doc_src['object_name']['source'])
        doc.mufile = file
        doc.zittingdatum = doc_src['dar_date_vergadering']['parsed'] if doc_src['dar_date_vergadering']['success'] else None
        doc.zittingnr = doc_src['dar_verg_nr']['parsed']
        doc.confidential = doc_src['dar_restricted']['parsed'] if doc_src['dar_restricted']['success'] else None
        doc.err_date = doc_src['dar_err_date']['parsed'] if doc_src['dar_err_date']['success'] else None
        doc.besl_vereist = doc_src['dar_besl_vereist']['parsed']
        doc.levenscyclus_status = doc_src['dar_levenscyclus_status']['parsed'] if doc_src['dar_levenscyclus_status']['success'] else None
        doc.pub_dates = doc_src['dar_pub_date']['parsed'] if doc_src['dar_pub_date']['success'] else None
        doc.title = title_from_dar_onderwerp(doc_src['dar_onderwerp']['parsed']) if doc_src['dar_onderwerp']['success'] and doc_src['dar_onderwerp']['parsed'] else None
        doc.description = description_from_dar_onderwerp(doc_src['dar_onderwerp']['parsed']) if doc_src['dar_onderwerp']['success'] and doc_src['dar_onderwerp']['parsed'] else None
        doc._indiener_refs = doc_src['dar_indiener_samenvatting']['parsed'] if doc_src['dar_indiener_samenvatting']['success'] else []
        if doc_src['dar_vorige']['success']:
            for doc_ref in doc_src['dar_vorige']['parsed']:
                r = {'source': doc_ref}
                try:
                    r['parsed'] = p_doc_name(doc_ref)
                    r['success'] = True
                except ValueError:
                    r['success'] = False
                doc._document_refs.append(r)
        documenten.append(doc)

        if doc_src['object_name']['success']:
            try:
                doc.parsed_name = doc_src['object_name']['parsed'][0]
            except TypeError:
                doc.parsed_name = doc_src['object_name']['parsed']
            if isinstance(doc.parsed_name, VersionedDocumentName):
                doc.version = doc_src['object_name']['parsed'][1]
            else:
                doc.version = None

            if 'dar_fiche_type' in doc_src: # Beslissingsfiches
                doc._type_ref = doc_src['dar_fiche_type']['parsed'] if doc_src['dar_fiche_type']['success'] else None

                if doc_src['dar_date_vergadering']['success']:
                    jaar = doc_src['dar_date_vergadering']['parsed']
                elif isinstance(doc.parsed_name, VrBeslissingsficheName):
                    jaar = doc.parsed_name.year
                elif isinstance(doc.parsed_name, OcBeslissingsficheName):
                    jaar = doc.parsed_name.datum.year
                else:
                    logging.warning("Couldn't determine session year from separate metadata field nor document name for document version {}".format(doc.source_name))
                if doc_src['dar_verg_nr']['success']:
                    zitting_nr = doc_src['dar_verg_nr']['parsed']
                elif isinstance(doc.parsed_name, VrBeslissingsficheName):
                    zitting_nr = doc.parsed_name.zitting_nr
                else:
                    logging.warning("Couldn't determine session number from separate metadata field nor document name for document version {}".format(doc.source_name))
                if doc_src['dar_volgnummer']['success']:
                    volgnr = doc_src['dar_volgnummer']['parsed']
                elif isinstance(doc.parsed_name, VrBeslissingsficheName) or isinstance(doc.parsed_name, OcBeslissingsficheName):
                    volgnr = doc.parsed_name.punt_nr
                else:
                    logging.warning("Couldn't determine agenda item number from separate metadata field nor document name for document version {}".format(doc.source_name))
                agendapunt = Agendapunt(jaar, zitting_nr, volgnr, doc)
                if isinstance(doc.parsed_name, VrBeslissingsficheName):
                    agendapunt.type = agendapunt.beslissingsfiche.parsed_name.punt_type # PUNT, MEDEDELING or VARIA
                agendapunt.besl_vereist = doc_src['dar_besl_vereist']['parsed']
                if doc_src['dar_rel_docs']['success']:
                    for doc_ref in doc_src['dar_rel_docs']['parsed']:
                        r = {'source': doc_ref}
                        try:
                            if doc_src['dar_context']['source'] == 'Vlaamse Regering':
                                r['parsed'] = p_doc_name(doc_ref)
                            elif doc_src['dar_context']['source'] == 'Overlegcomite':
                                r['parsed'] = p_oc_doc_name(doc_ref)
                            r['success'] = True
                        except ValueError:
                            r['success'] = False
                        agendapunt._document_refs.append(r)
                else:
                    agendapunt._document_refs = []
                agendapunten.append(agendapunt)
            else: # All other documents
                doc._type_ref = doc_src['dar_doc_type']['parsed'] if doc_src['dar_doc_type']['success'] else None

    return files, documenten, agendapunten

def group_doc_vers_by_source_name(doc_vers):
    doc_vers_by_source_name = {}
    for k, g in itertools.groupby(doc_vers, lambda doc: doc.source_name):
        matches = tuple(g)
        doc_vers_by_source_name[k] = matches
        if len(matches) > 1:
            logging.warning("Found {} instances of supposedly unique document '{}' (by source name): {}".format(len(matches), k, '\n\t- ' + '\n\t- '.join(tuple(str(doc.source_name) for doc in matches))))
    return doc_vers_by_source_name

def group_doc_vers_by_parsed_name(doc_vers):
    doc_vers_by_parsed_name = {}
    for k, g in itertools.groupby(doc_vers, lambda doc: doc.name):
        matches = tuple(g)
        doc_vers_by_parsed_name[k] = matches
        if len(matches) > 1:
            logging.warning("Found {} instances of supposedly unique document '{}' (by parsed name): {}".format(len(matches), k, '\n\t- ' + '\n\t- '.join(tuple(str(doc.name) for doc in matches))))
    return doc_vers_by_parsed_name

# Group documents by object id
def group_doc_vers_by_object_id(doc_vers):
    doc_vers_by_object_id = {}
    for k, g in itertools.groupby(doc_vers, lambda doc: doc.id):
        matches = tuple(g)
        if len(matches) == 1:
            doc_vers_by_object_id[k] = matches[0]
        else:
            logging.warning("Found {} instances of document with id '{}', choosing pdf-version: {}".format(len(matches), k, '\n\t- ' + '\n\t- '.join(tuple(str(doc) for doc in matches))))
            filtered = tuple(filter(lambda doc: bool(doc.mufile.extension == 'pdf'), matches))
            if len(filtered) == 1:
                doc_vers_by_object_id[k] = filtered[0]
            else:
                logging.error("Found {} pdf-versions of document with id '{}': {}".format(len(matches), k, '\n\t- ' + '\n\t- '.join(tuple(str(doc) for doc in matches))))
                doc_vers_by_object_id[k] = filtered[0]
                # raise Exception("Found {} pdf-versions of document with id '{}': {}".format(len(matches), k, '\n\t- ' + '\n\t- '.join(tuple(str(doc) for doc in matches)))) # TODO

    return doc_vers_by_object_id

# materialize references to other documents in documents
# n = 0
# m = 0
# i = 0
# for doc in ordinary_documenten:
#     i += 1
#     if doc.source['dar_vorige']:
#         n += len(doc.source['dar_vorige'])
#     if doc.source['dar_vervangt']:
#         n += len(doc.source['dar_vervangt'])
#     if doc.source['dar_aanvullend']:
#         n += len(doc.source['dar_aanvullend'])
#     doc.link_document_refs(documenten_by_stuknummer, key_fun.ref_by_stuknummer_parts)
#     m += len(doc.vorige)
#     m += len(doc.vervangt)
#     m += len(doc.aanvullend)
# logging.info("Found {} out of {} documents ({:.1f}%) referenced in {} documents".format(m, n, m/n*100, i))
