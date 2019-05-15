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
                dossiernr_doc_name = next(doc.parsed_name for doc in agendapunt.rel_docs if isinstance(doc.parsed_name, VrDocumentName))
                year = dossiernr_doc_name.datum.year
                dossiernr = dossiernr_doc_name.dossier_nr
                dossier_key = tuple((year, dossiernr))
            except StopIteration: # No document that contains a dossiernummer in this agendapunt
                logging.warning("No dossiernr found for agenda item {}".format(agendapunt))
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
    return dossiers
