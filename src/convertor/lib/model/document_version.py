#!/usr/bin/python3
import logging
import uuid

from rdflib.namespace import RDF, XSD
from rdflib import URIRef, Literal

from .document_name import VersionedDocumentName, VrBeslissingsficheName, VrDocumentName, VrNotulenName

def search_government(governments, date):
    for gov in governments:
        if date > gov.installation_date:
            if gov.resignation_date:
                if date < gov.resignation_date:
                    return gov
                continue
            else:
                return gov
        continue
    return None

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
        self.err_date = None
        self.levenscyclus_status = None
        self.pub_dates = None
        self.title = None
        self.short_title = None

        self.mufile = None
        self.vorige = []
        self.indieners = []

        self._type_ref = ''
        self._decision_doc_refs = []
        self._previous_doc_refs = []
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

    def link_document_refs(self, doc_lut, fallback_doc_lut):
        """ doc_list is a sorted list of all document objects than can be searched to link to these referenced documents"""
        if self._previous_doc_refs:
            self.vorige = []
            for rel_doc in self._previous_doc_refs:
                try:
                    self.vorige.append(doc_lut[rel_doc['source']][0]) # TEMP: As value for doc_lut key is a tuple of docs (because of ambiguity), only take the first one
                except KeyError as e:
                    try:
                        logging.info("No match found by source doc name ref '{}', trying search by parsed name ...".format(rel_doc['source']))
                        if rel_doc['success']:
                            try:
                                name = rel_doc['parsed'][0].versioned_name(rel_doc['parsed'][1])
                            except TypeError:
                                name = rel_doc['parsed'].name()
                            self.vorige.append(fallback_doc_lut[name][0]) # TEMP: As value for doc_lut key is a tuple of docs (because of ambiguity), only take the first one
                        else:
                            logging.info("Related doc {} doesn't have a parsed name".format(rel_doc['source']))
                    except KeyError as e:
                        logging.warning("No match found for related doc '{}''".format(rel_doc['source']))
        return self.vorige

    def link_indiener_refs(self, submitter_lut, governments):
        """ mandatee_lut takes keys of form str(ref)+gov.uuid (for mandatees) or str(ref) (for governing bodies)"""
        if self._indiener_refs:
            gov = search_government(governments, self._zittingdatum)
            self.indieners = []
            for indiener in self._indiener_refs:
                if gov:
                    try:
                        self.indieners.append(submitter_lut[str(indiener)+gov.uuid])
                    except KeyError:
                        pass
                try:
                    self.indieners.append(submitter_lut[str(indiener)])
                except KeyError:
                    logging.warning("No match found for indiener reference '{}'".format(indiener))
        return self.indieners

    @property
    def doc_type_uri(self):
        if isinstance(self.parsed_name, VrBeslissingsficheName):
            return 'http://kanselarij.vo.data.gift/id/concept/document-type-codes/2b73f8e2-b1f8-4cbd-927f-30c91759f08b'
        elif isinstance(self.parsed_name, VrDocumentName) and self.parsed_name.doc_type == 'DEC':
            return 'https://data.vlaanderen.be/id/concept/AardWetgeving/Decreet'
        elif isinstance(self.parsed_name, VrNotulenName):
            return 'http://kanselarij.vo.data.gift/id/concept/document-type-codes/e149294e-a8b8-4c11-83ac-6d4c417b079b'
        # elif self._type_ref
        #     if self._type_ref == 'Perkament':
        #         return 
        #     elif self._type_ref == 'Nota':
        #         return 
        #     elif self._type_ref == 'Notulen':
        #         return 
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
        if self.version:
            triples.append((uri, ns.EXT['versieNummer'], Literal(self.version)))
        else:
            triples.append((uri, ns.EXT['versieNummer'], Literal(1)))
        if self.mufile.created:
            triples.append((uri, ns.DCT['created'], Literal(self.mufile.created.isoformat().replace('+00:00', 'Z'), datatype=XSD.dateTime)))
        else:
            pass # FIXME (self.zittingdatum maybe?)
        # if self.title:
        #     triples.append((uri, ns.DCT['title'], Literal(self.title)))
        # if self.short_title:
        #     triples.append((uri, ns.EXT['omschrijving'], Literal(self.short_title)))
        # ext:idNumber # TODO
        triples.append((uri, ns.EXT['gekozenDocumentNaam'], Literal(self.source_name)))
        triples.append((uri, ns.EXT['file'], URIRef(self.mufile.uri(base_uri))))

        return triples
