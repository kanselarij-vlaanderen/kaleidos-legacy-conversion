#!/usr/bin/python3
import itertools
import logging

from .doris_export_parsers import p_doc_name, p_oc_doc_name
from .model.oc_document_version import DocumentVersion
from .model.document_name import VersionedDocumentName
from .create_files import create_file

def create_files_document_versions_agenda_items(parsed_import, src_base_uri, file_metadata_lut, file_uuid_lut=None):
    files = []
    document_versions = []
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
        doc._zittingdatum = doc_src['dar_date_vergadering']['parsed']
        doc._zittingnr = doc_src['dar_verg_nr']['parsed'] if doc_src['dar_verg_nr']['success'] else None
        doc._puntnr, doc._sub_puntnr = doc_src['dar_volgnummer']['parsed'] if doc_src['dar_volgnummer']['success'] else tuple([None, None])
        doc.confidential = doc_src['dar_restricted']['parsed'] if doc_src['dar_restricted']['success'] else True
        doc.err_date = doc_src['dar_err_date']['parsed'] if doc_src['dar_err_date']['success'] else None
        doc.besl_vereist = doc_src['dar_besl_vereist']['parsed']
        doc.levenscyclus_status = doc_src['dar_levenscyclus_status']['parsed'] if doc_src['dar_levenscyclus_status']['success'] else None
        doc.pub_dates = doc_src['dar_pub_date']['parsed'] if doc_src['dar_pub_date']['success'] else None
        doc.subject = doc_src['dar_onderwerp']['parsed'].strip() if doc_src['dar_onderwerp']['success'] else ''
        doc.keywords = doc_src['dar_keywords']['parsed'] if doc_src['dar_keywords']['parsed'] else []
        doc._indiener_refs = doc_src['dar_indiener_samenvatting']['parsed'] if doc_src['dar_indiener_samenvatting']['success'] else []
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
                            r['parsed'] = p_oc_doc_name(doc_ref)
                            r['success'] = True
                        except ValueError:
                            r['success'] = False
                        doc._decision_doc_refs.append(r)
                else:
                    doc._decision_doc_refs = None
            else: # All other documents
                doc._type_ref = doc_src['dar_doc_type']['parsed'] if doc_src['dar_doc_type']['success'] else None
    
            # if not doc._zittingdatum:
            #     if isinstance(doc.parsed_name, (VrDocumentName, AgendaName)):
            #         doc._zittingdatum = doc.parsed_name.datum
            #     else:
            #         logging.warning("Couldn't determine session date from separate metadata field nor document name for document version {}".format(doc.source_name))
            # if not doc._zittingnr:
            #     if isinstance(doc.parsed_name, (VrBeslissingsficheName, VrNotulenName)):
            #         doc._zittingnr = doc.parsed_name.zitting_nr
            #     else:
            #         logging.warning("Couldn't determine session number from separate metadata field nor document name for document version {}".format(doc.source_name))
            # if doc._puntnr is None:
            #     if isinstance(doc.parsed_name, VrBeslissingsficheName):
            #         doc._puntnr = doc.parsed_name.punt_nr
            #     else:
            #         logging.info("Couldn't determine agenda item number from separate metadata field nor document name for document version {}".format(doc.source_name))

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
