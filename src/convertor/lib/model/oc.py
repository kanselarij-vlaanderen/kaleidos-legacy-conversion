#!/usr/bin/python3
import uuid
from rdflib.namespace import RDF
from rdflib import URIRef, Literal
from pytz import timezone

TIMEZONE = timezone('Europe/Brussels')

class Session:
    def __init__(self, started_at):
        super().__init__()
        self.uuid = str(uuid.uuid1())

        self.started_at = started_at

        self.agenda_items = []
        self.agenda = None
        self.meeting_record = None

    def __str__(self):
        retval = "OC Agenda voor de zitting van {}".format(self.started_at)
        retval += '\n- agenda: {}'.format(self.agenda.name if self.agenda else '')
        retval += '\n- notulen: {}'.format(self.meeting_record.name if self.meeting_record else '')
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

        return triples


class AgendaItem():
    def __init__(self, priority, subject, sub_priority=None):
        super().__init__()
        self.uuid = str(uuid.uuid1())

        self.priority = priority
        self.sub_priority = sub_priority
        self.subject = subject
        self.submitter_uris = []
        self.case = None

        self.notification = None
        self.documents = []

    def __str__(self):
        retval = 'OC Punt {}{} ({}): {}'.format(self.priority, self.sub_priority if self.sub_priority else '', self.case, self.subject.split('\n')[0][:60] + ' ...')
        retval += '\nnotificatie: {}'.format(self.notification.name if self.notification else '')
        for doc in self.documents:
            retval += '\n * ' + doc.name
        return retval

    def uri(self, base_uri):
        return base_uri + "id/oc-agendapunten/" + "{}".format(self.uuid)

    def triples(self, ns, base_uri):
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.OC['priority'], Literal(self.priority)),
            (uri, ns.DCT['subject'], Literal(self.subject)),
        ]
        for submitter_uri in self.submitter_uris:
            triples.append((uri, ns.OC['submitter'], URIRef(submitter_uri)))
        if self.sub_priority:
            triples.append((uri, ns.OC['subPriority'], Literal(self.sub_priority)))
        if self.notification:
            triples.append((uri, ns.OC['notification'], URIRef(self.notification.uri(base_uri))))
        for doc in self.documents:
            triples += [
                (uri, ns.OC['files'], URIRef(doc.uri(base_uri))),
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
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.DCT['identifier'], Literal(self.identifier)),
        ]
        return triples
