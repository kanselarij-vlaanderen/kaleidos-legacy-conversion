#!/usr/bin/python3
import uuid
from rdflib.namespace import RDF
from rdflib import URIRef, Literal

class DocumentType:
    def __init__(self, label, abbreviation=None, description=None):
        super().__init__()
        self.uuid = str(uuid.uuid1())

        self.abbreviation = abbreviation
        self.label = label
        self.description = description

    def __str__(self):
        return "Document type {}".format(self.label)

    def uri(self, base_uri):
        return base_uri + "id/concept/document-type-code" + "/{}".format(self.uuid)

    def triples(self, ns, base_uri):
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.EXT['DocumentTypeCode']),
            (uri, RDF['type'], ns.SKOS['Concept']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.SKOS['prefLabel'], Literal(self.label)),
        ]
        if self.abbreviation:
            triples.append((uri, ns.SKOS['altLabel'], Literal(self.abbreviation)))
        if self.description:
            triples.append((uri, ns.SKOS['scopeNote'], Literal(self.description)))

        return triples
