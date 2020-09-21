#!/usr/bin/python3
import uuid

from rdflib.namespace import RDF, XSD
from rdflib import URIRef, Literal
import logging

from lib.code_lists.access_levels import ACCESS_LEVEL_URI

class Document:
    def __init__(self, first_document_version):
        super().__init__()
        self.src_uri = first_document_version.uri
        self.uuid = str(uuid.uuid1())

        try:
            self.title = first_document_version.parsed_name.name()
        except Exception:
            logging.info('No parsed name available for doc creation from version {}, using source name ...'.format(first_document_version.source_name))
            self.title = first_document_version.source_name
        self.created = first_document_version.mufile.created
        try:
            self.document_versions = [(first_document_version.version, first_document_version)]
        except AttributeError:
            self.document_versions = [(1, first_document_version)]
        self.doc_type_uri = first_document_version.doc_type_uri

    def __hash__(self):
        return self.uuid

    def __str__(self):
        return "OC Document {}".format(self.title)

    def uri(self, base_uri):
        return "{}id/documenten/{}".format(base_uri, self.uuid)

    def triples(self, ns, base_uri):
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.FOAF['Document']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.DCT['source'], URIRef(self.src_uri(base_uri))),
        ]
        if self.title:
            triples.append((uri, ns.DCT['title'], Literal(self.title)))
        if self.created:
            triples.append((uri, ns.DCT['created'], Literal(self.created.isoformat().replace('+00:00', 'Z'), datatype=XSD.dateTime)))
        for ver, doc in self.document_versions:
            triples.append((uri, ns.BESLUITVORMING['heeftVersie'], URIRef(doc.uri(base_uri))))
        if self.doc_type_uri:
            triples.append((uri, ns.EXT['documentType'], URIRef(self.doc_type_uri)))

        return triples
