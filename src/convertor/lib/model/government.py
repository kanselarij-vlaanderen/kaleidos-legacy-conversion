#!/usr/bin/python3
import uuid
from rdflib.namespace import RDF, XSD
from rdflib import URIRef, Literal

class Government:
    def __init__(self, name, installation_date, resignation_date=None):
        super().__init__()
        self.uuid = str(uuid.uuid1())
        self.src_uri = ""

        self.name = name
        self.prime_minister = None
        self.installation_date = installation_date
        self.resignation_date = resignation_date
        self.mandatees = []

    def __str__(self):
        return "{} ({} - {})".format(self.name, self.installation_date, self.resignation_date)

    def uri(self, base_uri):
        return base_uri + "id/bestuursorganen" + "/{}".format(self.uuid)

    def triples(self, ns, base_uri):
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.BESLUIT['Bestuursorgaan']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.DCT['source'], URIRef(self.src_uri)),
            (uri, ns.MANDAAT['bindingStart'], Literal(self.installation_date.isoformat(), datatype=XSD.date)),
        ]
        if self.resignation_date:
            triples.append((uri, ns.MANDAAT['bindingEinde'], Literal(self.resignation_date.isoformat(), datatype=XSD.date)))
        for mandatee in self.mandatees:
            triples.append((uri, ns.ORG['hasPost'], URIRef(mandatee.mandate_uri(base_uri))))
        return triples
