#!/usr/bin/python3
import itertools
import logging

from .doris_export_parsers import p_doc_name, p_oc_doc_name
from .model.document_version import DocumentVersion
from .model.document_name import VrBeslissingsficheName, VrDocumentName, AgendaName, VrNotulenName, VersionedDocumentName
from .create_files import create_file

def titles_from_dar_onderwerp(dar_onderwerp):
    """ returns tuple of forn (short_title, title) """
    try:
        lines = dar_onderwerp.splitlines()
    except AttributeError:
        return None, None
    n_lines = len(lines)
    if lines and lines[-1] == '':
        n_lines -= 1
    if n_lines == 1:
        return None, lines[0].strip()
    elif n_lines > 1:
        if lines[0].startswith(('-', 'A.', 'A ', 'A)')):
            return None, '\n'.join(lines).rstrip()
        else:
            return lines[0].strip(), '\n'.join(lines[1:]).rstrip()
    else:
        return None, None

def create_files_document_versions_agenda_items(parsed_import, src_base_uri, file_metadata_lut, file_uuid_lut=None):
    files = []
    document_versions = []
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
        doc.src_uri = src_base_uri + "{}-{}".format(doc.id, doc.mufile.extension) # object_ids in documentum arent unique, document type is needed for uniqueness
        doc._zittingdatum = doc_src['dar_date_vergadering']['parsed'] if doc_src['dar_date_vergadering']['success'] else None
        doc._zittingnr = doc_src['dar_verg_nr']['parsed']
        doc._puntnr = doc_src['dar_volgnummer']['parsed'] if doc_src['dar_volgnummer']['success'] else None
        doc.confidential = doc_src['dar_restricted']['parsed'] if doc_src['dar_restricted']['success'] else True
        doc.err_date = doc_src['dar_err_date']['parsed'] if doc_src['dar_err_date']['success'] else None
        doc.besl_vereist = doc_src['dar_besl_vereist']['parsed']
        doc.levenscyclus_status = doc_src['dar_levenscyclus_status']['parsed'] if doc_src['dar_levenscyclus_status']['success'] else None
        doc.pub_dates = doc_src['dar_pub_date']['parsed'] if doc_src['dar_pub_date']['success'] else None
        doc.short_title, doc.title = titles_from_dar_onderwerp(doc_src['dar_onderwerp']['parsed']) if doc_src['dar_onderwerp']['success'] else tuple(None, None)
        doc.keywords = doc_src['dar_keywords']['parsed'] if doc_src['dar_keywords']['parsed'] else []
        doc._indiener_refs = doc_src['dar_indiener_samenvatting']['parsed'] if doc_src['dar_indiener_samenvatting']['success'] else []
        if doc_src['dar_vorige']['success']:
            for doc_ref in doc_src['dar_vorige']['parsed']:
                r = {'source': doc_ref}
                try:
                    r['parsed'] = p_doc_name(doc_ref)
                    r['success'] = True
                except ValueError:
                    r['success'] = False
                doc._previous_doc_refs.append(r)
        document_versions.append(doc)

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
                        doc._decision_doc_refs.append(r)
                else:
                    doc._decision_doc_refs = None
            else: # All other documents
                doc._type_ref = doc_src['dar_doc_type']['parsed'] if doc_src['dar_doc_type']['success'] else None
    
            if not doc._zittingdatum:
                if isinstance(doc.parsed_name, (VrDocumentName, AgendaName)):
                    doc._zittingdatum = doc.parsed_name.datum
                else:
                    logging.warning("Couldn't determine session date from separate metadata field nor document name for document version {}".format(doc.source_name))
            if not doc._zittingnr:
                if isinstance(doc.parsed_name, (VrBeslissingsficheName, VrNotulenName)):
                    doc._zittingnr = doc.parsed_name.zitting_nr
                else:
                    logging.warning("Couldn't determine session number from separate metadata field nor document name for document version {}".format(doc.source_name))
            if doc._puntnr is None:
                if isinstance(doc.parsed_name, VrBeslissingsficheName):
                    doc._puntnr = doc.parsed_name.punt_nr
                else:
                    logging.info("Couldn't determine agenda item number from separate metadata field nor document name for document version {}".format(doc.source_name))

    return files, document_versions

def group_doc_vers_by_source_name(doc_vers):
    doc_vers_by_source_name = {}
    doc_vers = sorted(doc_vers, key=lambda doc: doc.source_name)
    for k, g in itertools.groupby(doc_vers, lambda doc: doc.source_name):
        matches = tuple(g)
        doc_vers_by_source_name[k] = matches
        if len(matches) > 1:
            logging.warning("Found {} instances of supposedly unique document '{}' (by source name): {}".format(len(matches), k, '\n\t- ' + '\n\t- '.join(tuple(str(doc.source_name) for doc in matches))))
    return doc_vers_by_source_name

def group_doc_vers_by_parsed_name(doc_vers):
    doc_vers_by_parsed_name = {}
    doc_vers = sorted(doc_vers, key=lambda doc: doc.name)
    for k, g in itertools.groupby(doc_vers, lambda doc: doc.name):
        matches = tuple(g)
        doc_vers_by_parsed_name[k] = matches
        if len(matches) > 1:
            logging.warning("Found {} instances of supposedly unique document '{}' (by parsed name): {}".format(len(matches), k, '\n\t- ' + '\n\t- '.join(tuple(str(doc.name) for doc in matches))))
    return doc_vers_by_parsed_name

# Group documents by object id
def group_doc_vers_by_object_id(doc_vers):
    doc_vers_by_object_id = {}
    doc_vers = sorted(doc_vers, key=lambda doc: doc.id)
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
