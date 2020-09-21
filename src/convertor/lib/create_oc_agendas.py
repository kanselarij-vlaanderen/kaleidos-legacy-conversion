#!/usr/bin/python3
import itertools
import logging

from .model.document_name import OcAgendaName, OcNotificatieName, VrNotulenName, VrDocumentName, OcVerslagName
from .model.oc import Session, AgendaItem

def by_session(doc):
    return doc._zittingdatum

def by_item(doc):
    return doc._puntnr, doc._sub_puntnr

def is_session_level_doc(doc):
    return isinstance(doc.parsed_name, OcAgendaName) or \
        isinstance(doc.parsed_name, OcVerslagName) or \
        doc.parsed_name is None or \
        doc._puntnr is None or \
        doc._puntnr == 0

def is_item_doc(doc): # All documents that are part of the agenda item
    return not is_session_level_doc(doc)

def is_notification(doc):
    return isinstance(doc.parsed_name, OcNotificatieName)

def is_unparsed(doc):
    return doc.parsed_name is None

# Create agendas with item structure out of fiches
def create_agendas(document_versions):
    sessions = []
    # Group by session (agenda)
    valid_doc_versions = list(filter(lambda d: (d._zittingdatum is not None), document_versions))
    valid_doc_versions = sorted(valid_doc_versions, key=by_session)
    docs_per_session = itertools.groupby(valid_doc_versions, by_session)
    for session_date, docs_1 in docs_per_session:
        docs_1 = list(docs_1)
        session = Session(session_date)
        sessions.append(session)
        session.src_uri = docs_1[0].src_uri
        try:
            session.documents = list(map(lambda d: d.document, filter(is_session_level_doc, docs_1)))
        except (TypeError, IndexError) as e:
            logging.warning("Didn't find meeting level docs for agenda {}\n{}".format(session.started_at, e))
        # Group by agenda item
        valid_item_docs = list(filter(is_item_doc, docs_1))
        valid_item_docs = sorted(valid_item_docs, key=by_item)
        docs_per_agenda_item = itertools.groupby(valid_item_docs, by_item)
        for item_numbers, docs_2 in docs_per_agenda_item:
            main_number, sub_number = item_numbers
            try:
                notification = list(filter(is_notification, docs_2))[0]
                item = AgendaItem(main_number, notification.subject, sub_number)
                item.notification = notification
                item.documents = list(map(lambda d: d.document, filter(lambda d: not is_notification(d), docs_2)))
                session.agenda_items.append(item)
            except (TypeError, IndexError):
                logging.warning("Didn't find notification for agenda {} item {}{}. Skipping ...".format(session.started_at, main_number, sub_number if sub_number else ''))
    # Sort agendas by date
    sessions.sort(key=lambda a: a.started_at)

    return sessions
