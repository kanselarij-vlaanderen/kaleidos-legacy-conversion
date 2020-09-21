#!/usr/bin/python3
import uuid
from rdflib.namespace import RDF
from rdflib import URIRef, Literal
from pytz import timezone
import logging
import textwrap

TIMEZONE = timezone('Europe/Brussels')

class Session:
    def __init__(self, started_at):
        super().__init__()
        self.uuid = str(uuid.uuid1())

        self.started_at = started_at

        self.agenda_items = []
        self.documents = []

    def __str__(self):
        retval = "OC Agenda voor de zitting van {}".format(self.started_at)
        if self.documents:
            retval += "\nDocumenten:"
        for doc in self.documents:
            retval += textwrap.indent("\n" + str(doc), "\t")
        retval += "\nAgendapunten:"
        for item in self.agenda_items:
            retval += textwrap.indent("\n" + str(item), "\t")

        return retval

    def uri(self, base_uri):
        return base_uri + "id/oc-zittingen/" + "{}".format(self.uuid)

    def triples(self, ns, base_uri): # DONE, except varia
        # Agenda
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.OC['Meeting']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.PROV['startedAtTime'], Literal(self.started_at)),
        ]

        for item in self.agenda_items:
            triples.append((uri, ns.OC['agendaItem'], URIRef(item.uri(base_uri))))

        for doc in self.documents:
            triples.append((uri, ns.OC['documents'], URIRef(doc.uri(base_uri))))

        return triples


class AgendaItem():
    def __init__(self, priority, subject, sub_priority=None):
        super().__init__()
        self.uuid = str(uuid.uuid1())

        self.priority = priority
        self.sub_priority = sub_priority
        self.subject = subject if subject else ''
        self.submitter_uris = []
        self.case = None

        self.notification = None
        self.documents = []

        self.notification_documents = []
        
    def __str__(self):
        retval = 'OC Punt {}{} ({}): {}'.format(self.priority, self.sub_priority if self.sub_priority else '', self.case, self.subject.split('\n')[0][:60] + ' ...')
        retval += '\n\tnotificatie: {}'.format(self.notification)
        if self.documents:
            retval += "\n\tdocumenten:"
        for doc in self.documents:
            retval += '\n\t\t * ' + str(doc)
        return retval

    def uri(self, base_uri):
        return base_uri + "id/oc-agendapunten/" + "{}".format(self.uuid)

    def link_document_refs(self, doc_lut):
        if self.notification and self.notification._decision_doc_refs:
            self.notification_documents = []
            for rel_doc in self.notification._decision_doc_refs:
                try:
                    doc = doc_lut[rel_doc['source']][0] # WARNING: As value for doc_lut key is a tuple of docs (because of ambiguity), only take the first one
                    self.notification_documents.append(doc)
                    if doc not in self.documents:
                        self.documents.append(doc)
                except KeyError as e:
                    logging.warning("No match found for notification-related doc '{}'".format(rel_doc['source']))
        return self.notification_documents

    def triples(self, ns, base_uri):
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.OC['AgendaItem']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.OC['priority'], Literal(self.priority)),
            (uri, ns.DCT['subject'], Literal(self.subject)),
        ]
        for submitter_uri in self.submitter_uris:
            triples.append((uri, ns.OC['submitter'], URIRef(submitter_uri)))
        if self.sub_priority:
            triples.append((uri, ns.OC['subPriority'], Literal(self.sub_priority)))
        if self.notification:
            triples.append((uri, ns.OC['notification'], URIRef(self.notification.document.uri(base_uri)))) # Link to document
        if self.case:
            triples.append((URIRef(self.case.uri(base_uri)), ns.OC['caseAgendaItem'], uri))
        for doc in self.documents:
            triples += [
                (uri, ns.OC['documents'], URIRef(doc.document.uri(base_uri))), # Link to document
            ]
        for doc in self.notification_documents:
            triples += [
                (uri, ns.OC['notificationRelatedDocuments'], URIRef(doc.uri(base_uri))), # link to document version
            ]
        return triples

class Case():
    def __init__(self, identifier):
        super().__init__()
        self.uuid = str(uuid.uuid1())
        self.identifier = identifier

    def __str__(self):
        return 'OC Dossier {}'.format(self.identifier)

    def uri(self, base_uri):
        return base_uri + "id/oc-dossiers/" + "{}".format(self.identifier)

    def triples(self, ns, base_uri):
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.OC['Case']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.DCT['identifier'], Literal(self.identifier)),
        ]
        return triples
