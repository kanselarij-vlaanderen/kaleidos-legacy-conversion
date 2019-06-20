#!/usr/bin/python3
import logging
import uuid

from rdflib.namespace import RDF, XSD
from rdflib import URIRef, Literal

class Mandatee:
    def __init__(self, person, start_date, end_date=None):
        super().__init__()
        self.src_uri = ''
        self.uuid = str(uuid.uuid1())
        self.mandate_uuid = str(uuid.uuid1())

        self.person = person
        self.start_date = start_date
        self.end_date = end_date
        self.official_title = None
        self.order = None
        self.mandate_uri = None
        self.policy_domains = []

        self.deprecated = False
    def __str__(self):
        return "{} ({} - {}) uuid {}: {}".format(str(self.person),
                                                 self.start_date,
                                                 self.end_date if self.is_active() else '...',
                                                 self.person.uuid,
                                                 self.official_title)

    def uri(self, base_uri):
        return base_uri + "id/mandatarissen" + "/{}".format(self.uuid)

    def is_active(self):
        return bool(self.end_date)

    def triples(self, ns, base_uri):
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.MANDAAT['Mandataris']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.DCT['source'], URIRef(self.src_uri)),
            (uri, ns.MANDAAT['start'], Literal(self.start_date.isoformat(), datatype=XSD.date)),
            (uri, ns.ORG['holds'], URIRef(self.mandate_uri)),
            (uri, ns.MANDAAT['isBestuurlijkeAliasVan'], URIRef(self.person.uri(base_uri))),
        ]
        if self.end_date:
            triples.append((uri, ns.MANDAAT['einde'], Literal(self.end_date.isoformat(), datatype=XSD.date)))
        if self.official_title:
            triples.append((uri, ns.DCT['title'], Literal(self.official_title)))
        if self.deprecated:
            triples.append((uri, ns.OWL['deprecated'], Literal(str(self.deprecated).lower(), datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))))

        return triples

class Person:
    def __init__(self, family_name, given_name=None):
        super().__init__()
        self.src_uri = ''
        self.uuid = str(uuid.uuid1())
        self.src_id = None

        self.given_name = given_name
        self.family_name = family_name

    def __str__(self):
        retval = self.family_name
        if self.given_name:
            retval += ', ' + self.given_name
        return retval

    def uri(self, base_uri):
        return base_uri + "id/personen" + "/{}".format(self.uuid)

    def triples(self, ns, base_uri):
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.PERSON['Person']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.DCT['source'], URIRef(self.src_uri)),
            (uri, ns.FOAF['familyName'], Literal(self.family_name)),
            # (uri, ns.FOAF['name'], Literal()),
        ]
        if self.given_name:
            triples.append((uri, ns.FOAF['firstName'], Literal(self.given_name)))

        return triples
