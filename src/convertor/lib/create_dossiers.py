#!/usr/bin/python3
import logging
import uuid

from .model.document_name import VrDocumentName
from .model.dossier import Dossier

def create_dossiers(agendas):
    """
    Returns list of Dossiers by year and dossiernummer,
    where each dossier-key corresponds to a list of agendapunten
    """
    dossiers = {}
    for agenda in agendas:
        for agendapunt in agenda.agendapunten:
            try:
                dossiernr_doc_name = next(doc.parsed_name for doc in agendapunt.documents if isinstance(doc.parsed_name, VrDocumentName))
                year = dossiernr_doc_name.datum.year
                dossiernr = dossiernr_doc_name.dossier_nr
                doc_type = dossiernr_doc_name.doc_type
                dossier_key = tuple((year, doc_type, dossiernr))
            except StopIteration: # No document that contains a dossiernummer in this agendapunt
                logging.info("No dossiernr found for agenda item {}".format(agendapunt))
                dossiernr = None
                dossier_key = str(uuid.uuid1())
            try:
                dossier = dossiers[dossier_key]
            except KeyError:
                dossier = Dossier(agendapunt.uri)
                dossiers[dossier_key] = dossier
                # dossier.type = dossier_doc.
                # dossier.aanmaakdatum = dossier_doc.
                dossier.titel = agendapunt.title
                if dossiernr:
                    dossier.nummer = dossiernr
            dossier.agendapunten.append(agendapunt)
            for rel_doc in agendapunt.documents:
                for doc in filter(lambda d: isinstance(d.parsed_name, VrDocumentName), rel_doc.vorige):
                    n = doc.parsed_name
                    try:
                        dossier.agendapunten += dossiers[(n.datum.year, n.doc_type, n.dossier_nr)].agendapunten
                    except KeyError:
                        pass
            dossier.agendapunten = list(set(dossier.agendapunten))
    return dossiers
