#!/usr/bin/python3
import itertools
import logging

from .model.document_name import AgendaName, VrBeslissingsficheName, VrNotulenName
from .model.agenda import Agenda, Agendapunt

def by_session(doc):
    return doc._zittingdatum, doc._zittingnr

def by_item(doc):
    return doc._puntnr

def is_agenda(doc):
    return isinstance(doc.parsed_name, AgendaName)

def is_notulen(doc):
    return isinstance(doc.parsed_name, VrNotulenName)

def is_bf(doc):
    return isinstance(doc.parsed_name, VrBeslissingsficheName)

def is_item_doc(doc): # All documents that are part of the agenda item
    return not isinstance(doc.parsed_name, (VrBeslissingsficheName, AgendaName))

def is_unparsed(doc):
    return doc.parsed_name is None

# Create agendas with item structure out of fiches
def create_agendas(document_versions):
    agendas = []
    # Group by session (agenda)
    valid_doc_versions = list(filter(lambda d: (d._zittingdatum is not None) and (d._zittingnr is not None), document_versions))
    valid_doc_versions = sorted(valid_doc_versions, key=by_session)
    docs_per_session = itertools.groupby(valid_doc_versions, by_session)
    for k, docs_1 in docs_per_session:
        docs_1 = list(docs_1)
        session_date, session_number = k
        agenda = Agenda(session_date, session_number)
        agenda.src_uri = docs_1[0].src_uri
        agendas.append(agenda)
        try:
            agenda.agenda_doc = list(filter(is_agenda, docs_1))[0] # Unversioned
        except (TypeError, IndexError):
            logging.warning("Didn't find agenda doc for agenda {}".format(agenda.datum))
        try:
            agenda.notulen = sorted(list(filter(is_notulen, docs_1)), key=lambda d: d.version)[-1] # Versioned
        except (TypeError, IndexError):
            logging.warning("Didn't find notulen doc for agenda {}".format(agenda.datum))
        # Group by agenda item
        valid_item_docs = list(filter(lambda d: d._puntnr is not None, docs_1))
        valid_item_docs = sorted(valid_item_docs, key=by_item)
        docs_per_agenda_item = itertools.groupby(valid_item_docs, by_item)
        for item_number, docs_2 in docs_per_agenda_item:
            docs_2 = list(docs_2)
            if item_number: # Regular items & new style announcements
                announcement = list(filter(lambda d: d._type_ref == 'Mededeling', docs_2))
                non_announcement = list(filter(lambda d: not (d._type_ref == 'Mededeling'), docs_2))
                for docs_3 in (announcement, non_announcement):
                    if docs_3:
                        item = Agendapunt(item_number)
                        item.src_uri = docs_3[0].src_uri
                        agenda.agendapunten.append(item)
                        try:
                            item.beslissingsfiche = sorted(list(filter(is_bf, docs_3)), key=lambda d: d.version if d.version else 0)[-1] # Versioned
                        except (TypeError, IndexError):
                            logging.warning("Didn't find beslissingsfiche doc for agenda {} item {}".format(agenda.datum, item_number))
                        item.documents = list(filter(is_item_doc, docs_3))
            else: # Old style announcements with decision (had no other docs, only ones coupled to decision)
                for beslissingsfiche in list(filter(is_bf, docs_2)):
                    item = Agendapunt(item_number, beslissingsfiche)
                    item.src_uri = beslissingsfiche.src_uri
                    agenda.agendapunten.append(item)
    # Sort agendas by date
    agendas.sort(key=lambda a: tuple((a.datum.year, a.zittingnr)))

    return agendas
