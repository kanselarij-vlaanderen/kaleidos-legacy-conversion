#!/usr/bin/python3
import uuid

from rdflib.namespace import RDF
from rdflib import URIRef, Literal

class Role:
    def __init__(self, label):
        super().__init__()
        self.uuid = str(uuid.uuid1())
        self.label = label

    def __str__(self):
        return self.label

    def uri(self, base_uri):
        return base_uri + "id/concept/bestuursfunctie-codes" + "/{}".format(self.uuid)

    def triples(self, ns, base_uri):
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.EXT['BestuursfunctieCode']),
            (uri, RDF['type'], ns.SKOS['Concept']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.SKOS['prefLabel'], Literal(self.label)),
            (uri, ns.SKOS['topConceptOf'], ns.EXT['BestuursfunctieCode']),
        ]
        return triples

