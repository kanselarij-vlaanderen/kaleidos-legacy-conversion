#!/usr/bin/python3
import uuid

from rdflib.namespace import RDF, XSD
from rdflib import URIRef, Literal

from lib.code_lists.access_levels import ACCESS_LEVEL_URI

class Document:
    def __init__(self, first_document_version):
        super().__init__()
        self.src_uri = first_document_version.uri
        self.uuid = str(uuid.uuid1())

        if first_document_version.title:
            self.title = first_document_version.title
        else:
            self.title = None
        self.created = first_document_version.mufile.created
        try:
            self.name = first_document_version.parsed_name.name()
            self.name_vr = self.name
        except AttributeError:
            self.name = first_document_version.source_name
            self.name_vr = None
        try:
            self.document_versions = [(first_document_version.version, first_document_version)]
        except AttributeError:
            self.document_versions = [(1, first_document_version)]
        self.doc_type_uri = first_document_version.doc_type_uri

    def __hash__(self):
        return self.uuid

    def __str__(self):
        return "Document {}: '{}'".format(self.name, self.title)

    @property
    def confidential(self):
        # No 'vertrouwelijk' at document-version level in new model, so better safe than sorry with 'any'
        return any(doc.confidential for ver, doc in self.document_versions)

    @property
    def access_level_uri(self):
        if self.confidential:
            return None
        elif any(doc.levenscyclus_status == 'Uitgesteld' for ver, doc in self.document_versions):
            return ACCESS_LEVEL_URI["Intern Regering"]
        elif any(doc.levenscyclus_status == 'Openbaar' for ver, doc in self.document_versions):
            if any(doc.in_news_item for ver, doc in self.document_versions):
                return ACCESS_LEVEL_URI["Publiek"]
            else:
                return ACCESS_LEVEL_URI["Intern Overheid"]
        else:
            return None
            
    def uri(self, base_uri):
        return "{}id/documenten/{}".format(base_uri, self.uuid)

    def triples(self, ns, base_uri):
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.FOAF['Document']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.DCT['source'], URIRef(self.src_uri(base_uri))),
        ]
        if self.confidential or (not self.access_level_uri):
            # Level "Intern kabinet" not included in initial implementation. Is regarded as equal to 'vertrouwelijk'
            confidential = 'true'
        else:
            confidential = 'false'
        triples.append((uri,
                        ns.EXT['vertrouwelijk'],
                        Literal(confidential, datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))))
        if self.access_level_uri:
            triples.append((uri,
                            ns.EXT['toegangsniveauVoorDocument'],
                            URIRef(self.access_level_uri)))
        if self.name:
            triples.append((uri, ns.BESLUITVORMING['stuknummerVR'], Literal(self.name)))
        if self.name_vr:
            triples.append((uri, ns.EXT['stuknummerVROriginal'], Literal(self.name_vr)))
        # if self.title:
        #     triples.append((uri, ns.DCT['title'], Literal(self.title)))
        # if self.description:
        #     triples.append((uri, ns.EXT['omschrijving'], Literal(self.description)))
        if self.created:
            triples.append((uri, ns.DCT['created'], Literal(self.created.isoformat().replace('+00:00', 'Z'), datatype=XSD.dateTime)))
        for ver, doc in self.document_versions:
            triples.append((uri, ns.BESLUITVORMING['heeftVersie'], URIRef(doc.uri(base_uri))))
        if self.doc_type_uri:
            triples.append((uri, ns.EXT['documentType'], URIRef(self.doc_type_uri)))

        return triples
