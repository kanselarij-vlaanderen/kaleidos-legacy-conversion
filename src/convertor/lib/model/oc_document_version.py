#!/usr/bin/python3
import logging
import uuid

from rdflib.namespace import RDF, XSD
from rdflib import URIRef, Literal

from .document_name import VersionedDocumentName, OcNotificatieName, OcVerslagName, OcDocumentName, OcNotulenName, OcAgendaName

from lib.code_lists.access_levels import ACCESS_LEVEL_URI

class DocumentVersion:
    """docstring for DocumentVersion."""
    def __init__(self, id, source_name, parsed_name=None):
        super().__init__()
        self.uuid = str(uuid.uuid1())
        self.id = id
        self.src_uri = ''
        self.source_name = source_name
        self.parsed_name = parsed_name

        self.version = None
        self.document = None # Reference to parent document
        self._zittingdatum = None
        self._zittingnr = None
        self._puntnr = None
        self.confidential = None
        self.levenscyclus_status = None
        self.title = None
        self.short_title = None
        self.keywords = []
        self.in_news_item = False

        self.mufile = None
        self.vorige = []
        self.indieners = []

        self._type_ref = ''
        self._decision_doc_refs = []
        self._indiener_refs = []

    def __str__(self):
        return self.source_name +  " ({})".format(self.mufile.extension)

    @property
    def name(self):
        if self.parsed_name:
            if isinstance(self.parsed_name, VersionedDocumentName) and self.version:
                return self.parsed_name.versioned_name(self.version)
            else:
                return self.parsed_name.name()
        else:
            raise AttributeError("Document '{}' has no parsed name".format(str(self)))

    @property
    def doc_type_uri(self):
        if isinstance(self.parsed_name, OcNotificatieName):
            return 'http://kanselarij.vo.data.gift/id/concept/document-type-codes/ee8bb6f1-5bcb-45b5-afd3-b103ef185a2b'
        elif isinstance(self.parsed_name, OcNotulenName):
            return 'http://kanselarij.vo.data.gift/id/concept/document-type-codes/e149294e-a8b8-4c11-83ac-6d4c417b079b'
        elif isinstance(self.parsed_name, OcAgendaName):
            return 'http://kanselarij.vo.data.gift/id/concept/document-type-codes/90bf0f69-295f-4324-bed8-910c4016d895'
        elif isinstance(self.parsed_name, OcVerslagName):
            return 'http://kanselarij.vo.data.gift/id/concept/document-type-codes/436a37c1-ecf0-44a4-8d44-7440c4a89df6'
        else:
            return None

    @property
    def access_level_uri(self):
        if self.confidential:
            return None
        elif self.levenscyclus_status == 'Uitgesteld':
            return ACCESS_LEVEL_URI["Intern Regering"]
        elif self.levenscyclus_status == 'Openbaar':
            return ACCESS_LEVEL_URI["Parlement"]
        else:
            return None

    def uri(self, base_uri):
        return base_uri + "id/document-versies/" + "{}".format(self.uuid)

    def triples(self, ns, base_uri):
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.EXT['DocumentVersie']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.DCT['source'], URIRef(self.src_uri)),
        ]
        version = self.version if self.version else 1
        triples.append((uri, ns.EXT['versieNummer'], Literal(version)))
        if self.mufile.created:
            triples.append((uri,
                            ns.DCT['created'],
                            Literal(self.mufile.created.isoformat().replace('+00:00', 'Z'), datatype=XSD.dateTime)))
        if self.confidential or (not self.access_level_uri):
            confidential = 'true'
        else:
            confidential = 'false'
        triples.append((uri,
                        ns.EXT['vertrouwelijk'],
                        Literal(confidential, datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))))
        if self.access_level_uri:
            triples.append((uri,
                            ns.EXT['toegangsniveauVoorDocumentVersie'],
                            URIRef(self.access_level_uri)))
        triples.append((uri, ns.EXT['file'], URIRef(self.mufile.uri(base_uri))))

        return triples
