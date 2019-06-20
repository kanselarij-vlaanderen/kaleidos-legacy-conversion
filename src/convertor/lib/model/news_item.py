#!/usr/bin/python3
import logging
import uuid

from rdflib.namespace import RDF, XSD
from rdflib import URIRef, Literal

class Theme:
    def __init__(self, label):
        super().__init__()
        self.src_uri = ''
        self.uuid = str(uuid.uuid1())
        self.id = None
        self.label = label
        self.deprecated = False

    def __str__(self):
        return self.label

    def uri(self, base_uri):
        return base_uri + "id/concept/thema-codes" + "/{}".format(self.uuid)

    def triples(self, ns, base_uri):
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.EXT['ThemaCode']),
            (uri, RDF['type'], ns.SKOS['Concept']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.DCT['source'], URIRef(self.src_uri)),
            (uri, ns.SKOS['prefLabel'], Literal(self.label)),
            (uri, ns.SKOS['topConceptOf'], ns.EXT['ThemaCode']),
        ]
        if self.deprecated:
            triples.append((uri, ns.OWL['deprecated'], Literal(str(self.deprecated).lower(), datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))))

        return triples

class NewsItem:
    def __init__(self, id, date, title, plaintext_body, structuredtext_body):
        super().__init__()
        self.src_uri = ''
        self.uuid = str(uuid.uuid1())
        self.id = id
        self.agenda_date = date
        self.public = False
        self.title = title
        self.date_published = None
        self.documents_date_published = None
        self.plaintext_body = plaintext_body
        self.structuredtext_body = structuredtext_body
        self.agenda_item_nr = None
        self.agenda_item_type = None
        self.theme_refs = []
        self.themes = []
        self.mandatee_refs = []
        self.mandatees = []
        self.document_refs = []
        self.document_versions = []

    def __str__(self):
        return "{} {} {}: {}".format(self.agenda_date, self.agenda_item_type, self.agenda_item_nr, self.title)

    def uri(self, base_uri):
        return base_uri + "id/nieuwsbrief-infos" + "/{}".format(self.uuid)

    def link_theme_refs(self, theme_lut, key_fun):
        if self.theme_refs:
            self.themes = []
            for theme_ref in self.theme_refs:
                try:
                    self.themes.append(theme_lut[key_fun(theme_ref)])
                except KeyError as e:
                    logging.warning('No match found for \'theme ref\' {}'.format(theme_ref))

    def link_mandatee_refs(self, mandatee_lut, key_fun):
        if self.mandatee_refs:
            self.mandatees = []
            for mandatee_ref in self.mandatee_refs:
                try:
                    self.mandatees += list(mandatee_lut[key_fun(mandatee_ref)])
                except KeyError as e:
                    if mandatee_ref == 115879:
                        # TODO: Vlaamse Regering
                        pass
                    elif mandatee_ref == 68473:
                        # TODO: Vlaamse overheid
                        pass
                    elif mandatee_ref == 115882:
                        # TODO: Vlaams Parlement
                        pass
                    else:
                        logging.warning('No match found for \'mandatee ref\' {}'.format(mandatee_ref))

    def link_document_refs(self, document_version_lut, key_fun):
        if self.document_refs:
            self.document_versions = []
            for document_ref in self.document_refs:
                try:
                    self.document_versions.append(document_version_lut[key_fun(document_ref)])
                except KeyError as e:
                    logging.warning('No match found for \'document ref\' {}'.format(document_ref))

    def triples(self, ns, base_uri):
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.BESLUITVORMING['NieuwsbriefInfo']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.DCT['source'], URIRef(self.src_uri)),
            (uri, ns.DCT['title'], Literal(self.title)),
            (uri, ns.BESLUITVORMING['inhoud'], Literal(self.plaintext_body)),
            (uri, ns.EXT['htmlInhoud'], Literal(self.structuredtext_body)),
            (uri, ns.EXT['afgewerkt'], Literal(str(self.public).lower(), datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))),
            # (uri, ns.DBPEDIA['subtitle'], Literal(self.title)), # don't have
        ]
        if self.public and self.date_published: # FIXME: are not effective, but planned dates in legacy data
            triples.append((uri, ns.DCT['issued'], Literal(self.date_published.isoformat(), datatype=XSD.dateTime)))
        if self.public and self.documents_date_published:
            triples.append((uri, ns.EXT['issuedDocDate'], Literal(self.documents_date_published.isoformat(), datatype=XSD.dateTime)))
        for theme in self.themes:
            triples.append((uri, ns.EXT['themesOfSubcase'], URIRef(theme.uri(base_uri))))
        for doc_ver in self.document_versions:
            triples.append((uri, ns.EXT['documentenVoorPublicatie'], URIRef(doc_ver.uri(base_uri))))
        return triples
