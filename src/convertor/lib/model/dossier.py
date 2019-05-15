#!/usr/bin/python3
import logging
import textwrap
import uuid
from rdflib.namespace import RDF
from rdflib import URIRef, Literal

class Dossier:
    def __init__(self, src_uri_fun):
        super().__init__() 
        self.uuid = str(uuid.uuid1())
        self.src_uri = src_uri_fun

        self.type = None
        self.aanmaakdatum = None
        self.korte_titel = None
        self.titel = None
        self.nummer = None

        self.agendapunten = []
        self.agenda = None

    def __str__(self):
        return "Dossier {}: '{}' ({})".format(self.nummer, self.korte_titel, self.aanmaakdatum)

    def uri(self, base_uri):
        return base_uri + "id/dossiers" + "/{}".format(self.uuid)

    def triples(self, ns, base_uri):
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.DBPEDIA['Case']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.DCT['source'], URIRef(self.src_uri(base_uri))),
            # (uri, ns.DCT['alternative'], Literal(self.agendapunt.beslissingsfiche.)),
            # (uri, ns.ADMS['identifier'], Literal(self.nummer)),
            (uri, ns.EXT['isGearchiveerd'], Literal(False, datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))),
            # (uri, ns.EXT['beleidsNiveau'], URIRef()),
        ]
        if self.aanmaakdatum:
            triples.append((uri, ns.DCT['created'], Literal(self.aanmaakdatum)))
        if self.nummer:
            triples.append((uri, ns.ADMS['identifier'], Literal(self.nummer)))
        if self.titel:
            triples.append((uri, ns.DCT['title'], Literal(self.titel)))
        for agendapunt in self.agendapunten:
            triples.append((uri, ns.DCT['hasPart'], URIRef(agendapunt.procedurestap_uri(base_uri))))
        # (uri, ns.DCT['type'], Literal(self.titel)) # PWC mentions 'Aktename'/'Beslissing', Kaleidos app 'Ter beslissing op de Minister Raad van de Vlaamse regering'
        
            # (uri, ns.DCT['relation'], URIRef(self.titel)),
            # 
            # (uri, ns.DCT['hasPart'], URIRef()),
            # 
            # zitting_uri
        # for bevoegde in self.bevoegden:
        #     triples.append((uri, ns.??['??'], URIRef(bevoegde.uri(base_uri))))
        # for thema in self.themas:
        #     triples.append((uri, ns.??['??'], URIRef(thema.uri(base_uri))))
        return triples
