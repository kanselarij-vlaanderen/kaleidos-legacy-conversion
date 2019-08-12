#!/usr/bin/python3
import uuid
from rdflib.namespace import RDF, XSD
from rdflib import URIRef, Literal

class GoverningBody:
    def __init__(self, name, installation_date=None, resignation_date=None):
        super().__init__()
        self.uuid = str(uuid.uuid1())
        self.src_uri = ""

        self.name = name
        
        # Properties bestuursorgaan in de tijd
        self.installation_date = installation_date
        self.resignation_date = resignation_date
        self.mandatees = []
        
        # Properties generic bestuursorgaan
        self.deprecated = False

    def __str__(self):
        if self.installation_date:
            return "Bestuursorgaan in de tijd: {} ({} - {})".format(self.name, self.installation_date, self.resignation_date if self.resignation_date else '...')
        else:
            return "Bestuursorgaan: {}{}".format(self.name, ' (ongekend in mapping)' if self.deprecated else '')

    def uri(self, base_uri):
        return base_uri + "id/bestuursorganen" + "/{}".format(self.uuid)

    def triples(self, ns, base_uri, src_base_uri=None):
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.BESLUIT['Bestuursorgaan']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.DCT['source'], URIRef(self.src_uri)),
            (uri, ns.SKOS['prefLabel'], Literal(self.name)),
        ]
        if self.installation_date:
            triples.append((uri, ns.MANDAAT['bindingStart'], Literal(self.installation_date.isoformat(), datatype=XSD.date)))
        if self.resignation_date:
            triples.append((uri, ns.MANDAAT['bindingEinde'], Literal(self.resignation_date.isoformat(), datatype=XSD.date)))
        for mandatee in self.mandatees:
            triples.append((uri, ns.ORG['hasPost'], URIRef(mandatee.mandate_uri(base_uri))))
        if self.deprecated:
            triples.append((uri, ns.OWL['deprecated'], Literal(str(self.deprecated).lower(), datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))))
        return triples
