#!/usr/bin/python3
import uuid

from rdflib.namespace import RDF, XSD
from rdflib import URIRef, Literal

class Document:
    def __init__(self, first_document_version):
        super().__init__()
        self.source = first_document_version
        self.uuid = str(uuid.uuid1())

        if first_document_version.title:
            self.title = first_document_version.title
        else:
            self.title = None
        if first_document_version.description:
            self.description = first_document_version.description
        else:
            self.description = None
        self.created = first_document_version.mufile.created
        try:
            self.name = first_document_version.name
        except AttributeError:
            self.name = first_document_version.source_name
        try:
            self.document_versions = {first_document_version.version: first_document_version}
        except AttributeError:
            self.document_versions = {1: first_document_version}
        self.type = first_document_version.type

    def __hash__(self):
        return self.uuid

    def __str__(self):
        return "Document {}: '{}'".format(self.name, self.title)

    @property
    def confidential(self):
        any(doc.confidential for ver, doc in self.document_versions.items()) # No 'vertrouwelijk' at document-version level in new model, so better safe than sorry with 'any'

    def src_uri(self, base_uri):
        return self.source.uri(base_uri)

    def uri(self, base_uri):
        return "{}id/documenten/{}".format(base_uri, self.uuid)

    def triples(self, ns, base_uri):
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.FOAF['Document']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.DCT['source'], URIRef(self.src_uri(base_uri))),
            # (uri, ns.BESLUITVORMING['stuknummerVR'], Literal('????')),
            # (uri, ns.??['??'], Literal(self.confidential)), # TODO confidentiality model?
        ]
        if self.title:
            triples.append((uri, ns.DCT['title'], Literal(self.title)))
        if self.description:
            triples.append((uri, ns.EXT['omschrijving'], Literal(self.description)))
        if self.created:
            triples.append((uri, ns.DCT['created'], Literal(self.created, datatype=XSD.dateTime)))
        for ver, doc in self.document_versions.items():
            triples.append((uri, ns.BESLUITVORMING['heeftVersie'], URIRef(doc.uri(base_uri))))
        if self.type:
            triples.append((uri, ns.EXT['documentType'], URIRef(self.type.uri())))

        return triples
