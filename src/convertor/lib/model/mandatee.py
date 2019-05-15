#!/usr/bin/python3
import logging
import uuid

from rdflib.namespace import RDF, XSD
from rdflib import URIRef, Literal

class Mandate:
    def __init__(self, role_ref):
        super().__init__()
        self.uuid = str(uuid.uuid1())
        self.src_id = None

        self.role_ref = role_ref
        self.role = None

    def __str__(self):
        return "Mandaat van {}".format(self.role.label)

    def src_uri(self, src_base_uri):
        return src_base_uri + "node" + "/{}".format(self.src_id)

    def uri(self, base_uri):
        return base_uri + "id/mandaten" + "/{}".format(self.uuid)

    def materializeRoleRef(self, role_lut, key_fun):
        if self.role_ref:
            try:
                self.role = role_lut[key_fun(self.role_ref)]
            except KeyError:
                logging.warning('No match found for \'role ref\' {}'.format(self.role_ref))

    def triples(self, ns, base_uri, src_base_uri):
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.MANDAAT['Mandaat']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.DCT['source'], URIRef(self.src_uri(src_base_uri))),
            (uri, ns.ORG['role'], URIRef(self.role.uri(base_uri)))
        ]
        return triples

class Mandatee:
    def __init__(self, person, start_date, end_date=None):
        super().__init__()
        self.uuid = str(uuid.uuid1())
        self.mandate_uuid = str(uuid.uuid1())

        self.person = person
        self.start_date = start_date
        self.end_date = end_date
        self.official_title = None
        self.order = None
        self.mandate = None
        self.policy_domains = []

    def __str__(self):
        return "{} ({} - {}) uuid {}: {}".format(str(self.person),
                                                 self.start_date,
                                                 self.end_date if self.is_active() else '...',
                                                 self.person.uuid,
                                                 self.official_title)

    def src_uri(self, src_base_uri):
        raise NotImplementedError("Please Implement this method")

    def uri(self, base_uri):
        return base_uri + "id/mandatarissen" + "/{}".format(self.uuid)

    def mandate_uri(self, base_uri):
        return base_uri + "id/mandaten" + "/{}".format(self.mandate_uuid)

    def is_active(self):
        return bool(self.end_date)

    def triples(self, ns, base_uri, src_base_uri):
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.MANDAAT['Mandataris']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.DCT['source'], URIRef(self.src_uri(src_base_uri))),
            (uri, ns.MANDAAT['start'], Literal(self.start_date.isoformat(), datatype=XSD.date)),
            (uri, ns.ORG['holds'], URIRef(self.mandate_uri(base_uri))),
            (uri, ns.MANDAAT['isBestuurlijkeAliasVan'], URIRef(self.person.uri(base_uri))),
        ]
        if self.end_date:
            triples.append((uri, ns.MANDAAT['einde'], Literal(self.end_date.isoformat(), datatype=XSD.date)))

        return triples

class Person:
    def __init__(self, family_name, given_name=None):
        super().__init__()
        self.uuid = str(uuid.uuid1())
        self.src_id = None

        self.given_name = given_name
        self.family_name = family_name

    def __str__(self):
        retval = self.family_name
        if self.given_name:
            retval += ', ' + self.given_name
        return retval

    def src_uri(self, src_base_uri):
        raise NotImplementedError("Please Implement this method")

    def uri(self, base_uri):
        return base_uri + "id/personen" + "/{}".format(self.uuid)

    def triples(self, ns, base_uri, src_base_uri):
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.PERSON['Person']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.DCT['source'], URIRef(self.src_uri(src_base_uri))),
            (uri, ns.FOAF['familyName'], Literal(self.family_name)),
            # (uri, ns.FOAF['name'], Literal()),
        ]
        if self.given_name:
            triples.append((uri, ns.FOAF['firstName'], Literal(self.given_name)))

        return triples
