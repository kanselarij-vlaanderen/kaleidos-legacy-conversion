#!/usr/bin/python3
import uuid

from rdflib.namespace import RDF, XSD
from rdflib import URIRef, Literal

class Publicatie:
    def __init__(self, datum, korte_titel=None):
        super().__init__()
        self.uuid = str(uuid.uuid1())
        self.src_uri = ""

        self.korte_titel = korte_titel
        self.datum = datum
        self.bevoegden = []
        self.themas = []

    def __str__(self):
        return "Publicatie {}".format(self.datum)

    def uri(self, base_uri):
        return base_uri + "id/publicaties" + "/{}".format(self.uuid)

    def triples(self, ns, base_uri):
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.BESLUITVORMING['Publicatie']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.DCT['source'], URIRef(self.src_uri)),
            (uri, ns.BESLUITVORMING['uiterstePublicatiedatum'], Literal(self.datum, datatype=XSD.date)),
        ]
        for bevoegde in self.bevoegden:
            triples.append((uri, ns.BESLUITVORMING['heeftBevoegde'], URIRef(bevoegde.uri(base_uri))))
        return triples
