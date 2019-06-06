#!/usr/bin/python3
import logging
import datetime
import textwrap
import uuid
from rdflib.namespace import RDF, XSD
from rdflib import URIRef, Literal
from pytz import timezone

from .publicatie import Publicatie

TIMEZONE = timezone('Europe/Brussels')

def find(l, match_fun):
    found = list(filter(match_fun, l))
    if not found:
        # logging.warning('No match found for \'{}\''.format(type(l[0]).__name__))
        return None
    elif len(found) > 1:
        logging.warning('More than 1 match ({}) found for \'{}\', now:\n{}'.format(len(found), type(l[0]).__name__, tuple(str(elem) for elem in found)))
    return found[0]

def find_agenda(agendas, date, verg_nr):
    return find(agendas, lambda agenda: agenda.datum == date and agenda.zittingnr == verg_nr)

def find_agenda_document(agenda_documenten, date, verg_nr):
    return find(agenda_documenten, lambda doc: doc.parsed_name.datum == date and doc.zittingnr == verg_nr)

def find_notulen_document(notulen_documenten, date, zittingnr):
    return find(notulen_documenten, lambda doc: doc.parsed_name.jaar == date.year and doc.zittingnr == zittingnr)

def find_oc_notulen_document(notulen_documenten, date, zittingnr):
    return find(notulen_documenten, lambda doc: doc.parsed_name.datum == date and (doc.zittingnr == zittingnr if doc.zittingnr else True))

class Agenda:
    """docstring for Agenda."""
    def __init__(self, datum, zittingnr):
        super().__init__()
        self.uuid = str(uuid.uuid1())

        self.zitting_uuid = str(uuid.uuid1())

        self.datum = datum
        self.zittingnr = zittingnr

        self.agendapunten = []
        self.notulen = None
        self.agenda_doc = None

    def __str__(self):
        retval = "Agenda voor zitting {:04d}/{:02d} ({}):".format(self.datum.year,
                                                                  self.zittingnr,
                                                                  self.datum)
        retval += "\n\tPunten:\n"
        for punt in self.punten:
            retval += textwrap.indent(str(punt) + '\n', '\t\t')
        retval += "\n\tMededelingen:\n"
        for mededeling in self.mededelingen:
            retval += textwrap.indent(str(mededeling) + '\n', '\t\t')
        retval += "\n\tVaria:\n"
        for varia in self.varia:
            retval += textwrap.indent(str(varia) + '\n', '\t\t')
        retval += "\n\n\tNotulen:\n"
        if self.notulen:
            retval += textwrap.indent(str(self.notulen) + '\n', '\t\t')
        retval += "\n\n\tAgenda document:\n"
        if self.agenda_doc:
            retval += textwrap.indent(str(self.agenda_doc) + '\n', '\t\t')

        return retval

    @property
    def punten(self):
        return sorted(filter(lambda p: p.type == 'PUNT', self.agendapunten), key=lambda p: p.volgnr if p.volgnr else 0) # FIXME sortt returns None

    @property
    def mededelingen(self):
        return list(filter(lambda p: p.type == 'MEDEDELING', self.agendapunten))

    @property
    def varia(self):
        return list(filter(lambda p: p.type == 'VARIA', self.agendapunten))

    def link_agenda_doc(self, agenda_docs):
        agenda_doc = find_agenda_document(agenda_docs, self.datum, self.zittingnr)
        if agenda_doc:
            self.agenda_doc = agenda_doc
        else:
            logging.warning("Didn't find doc for agenda {}".format(self.datum))
        return self.agenda_doc

    def link_notulen_doc(self, notulen_docs):
        try:
            notulen_doc = find_notulen_document(notulen_docs, self.datum, self.zittingnr)
        except AttributeError:
            notulen_doc = find_oc_notulen_document(notulen_docs, self.datum, self.zittingnr)
        if notulen_doc:
            self.notulen = notulen_doc
        else:
            logging.warning("Didn't find notulen for agenda {}".format(self.datum))
        return self.notulen

    def uri(self, base_uri):
        return base_uri + "id/agendas/" + "{}".format(self.uuid)

    def zitting_uri(self, base_uri):
        return base_uri + "id/zittingen/" + "{}".format(self.zitting_uuid)

    def triples(self, ns, base_uri): # DONE, except varia
        # Agenda
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.BESLUITVORMING['Agenda']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.EXT['finaleVersie'], Literal(True, datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))),
            (uri, ns.EXT['agendaNaam'], Literal('A')),
            (uri, ns.EXT['accepted'], Literal(True, datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))),
            (uri, ns.BESLUIT['isAangemaaktVoor'], URIRef(self.zitting_uri(base_uri))),
        ]

        # Zitting
        zitting_uri = URIRef(self.zitting_uri(base_uri))
        zitting_triples = [
            (zitting_uri, RDF['type'], ns.BESLUIT['Zitting']),
            (zitting_uri, ns.MU['uuid'], Literal(self.zitting_uuid)),
            (zitting_uri, ns.DCT['source'], URIRef(self.uri(base_uri))),
            (zitting_uri, ns.BESLUIT['geplandeStart'], Literal(TIMEZONE.localize(datetime.datetime.combine(self.datum, datetime.time(12, 0, 0))).isoformat(), datatype=XSD.dateTime)),
            # (zitting_uri, ns.PROV['startedAtTime'], Literal()),
            # (zitting_uri, ns.PROV['endedAtTime'], Literal()),
            (zitting_uri, ns.ADMS['identifier'], Literal(self.zittingnr)),
            (zitting_uri, ns.EXT['finaleZittingVersie'], Literal(True, datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))),
            (zitting_uri, ns.BESLUITVORMING['behandelt'], uri)
        ]

        # Agenda & Zitting
        for punt in self.agendapunten:
            zitting_triples.append((zitting_uri, ns.BESLUITVORMING['isAangevraagdVoor'], URIRef(punt.uri(base_uri))))
            triples.append((uri, ns.DCT['hasPart'], URIRef(punt.uri(base_uri))))

        return triples + zitting_triples


class Agendapunt():
    """docstring for Agendapunt."""
    def __init__(self, jaar, zittingnr, volgnr, beslissingsfiche):
        super().__init__()
        self.uuid = str(uuid.uuid1())
        self.procedurestap_uuid = str(uuid.uuid1())
        self.jaar = jaar
        self.zittingnr = zittingnr
        self.volgnr = volgnr

        self.type = None
        self.zitting = None
        self.besl_vereist = None

        self.beslissingsfiche = beslissingsfiche
        self.rel_docs = [] # Zowel documenten als notulen
        self.publicaties = []
        if self.beslissingsfiche.pub_dates:
            for date, key in self.beslissingsfiche.pub_dates:
                self.publicaties.append(Publicatie(date, key))  # Key as title ('A' for example)

        self.news_item = None


        self._document_refs = []
        self.gerelateerde_procedurestappen_uris = []

    def __str__(self):
        if self.type == 'PUNT':
            retval = self.type + ' ' + str(self.volgnr) + '\n'
        else:
            retval = str(self.type) + '\n'
        for doc in self.rel_docs:
            retval += textwrap.indent(str(doc) + '\n', '\t')
        return retval

    @property
    def title(self):
        title = self.beslissingsfiche.title
        if self.type == 'VARIA':
            if title:
                title = 'VARIA: ' + title
            else:
                title = 'VARIA'
        return title

    def link_document_refs(self, doc_lut, fallback_doc_lut):
        if self._document_refs:
            self.rel_docs = []
            for rel_doc in self._document_refs:
                try:
                    self.rel_docs.append(doc_lut[rel_doc['source']][0]) # TEMP: As value for doc_lut key is a tuple of docs (because of ambiguity), only take the first one
                except KeyError as e:
                    try:
                        logging.info('No match found by literal \'dar_rel_docs\'-key {}, trying search by properties'.format(rel_doc['source']))
                        if rel_doc['success']:
                            self.rel_docs.append(fallback_doc_lut[rel_doc['parsed']][0]) # TEMP: As value for doc_lut key is a tuple of docs (because of ambiguity), only take the first one
                        else:
                            logging.warning('Related doc {} doesn\'t have parsed parts'.format(rel_doc['source']))
                    except KeyError as e:
                        logging.warning('No match found for \'related\' doc {}'.format(rel_doc['source']))
        return self.rel_docs

    def link_news_item(self, news_item_lut):
        try:
            for ni in news_item_lut[self.beslissingsfiche.zittingdatum]:
                if ni.agenda_item_nr == self.volgnr and ni.agenda_item_type == self.type:
                    self.news_item = ni
                    break
        except KeyError:
            if self.is_beslist():
                logging.warning("Didn't find news item for agenda item {} that was decided upon".format(str(self)))
        return self.news_item

    def link_subcase_refs(self, dossiers, procedurestap_base_uri):
        self.gerelateerde_procedurestappen_uris = []
        for doc in (self.rel_docs + [self.beslissingsfiche]):
            for vorig_doc in doc.vorige:
                try:
                    if (vorig_doc.datum.year != doc.datum.year) and (vorig_doc.dossier_nr != doc.dossier_nr):
                        try:
                            rel_dossier = dossiers[(vorig_doc.datum.year, vorig_doc.dossier_nr)]
                        except KeyError:
                            continue
                        for ap in rel_dossier.agendapunten:
                            if vorig_doc in ap.rel_docs:
                                procedurestap_uri = ap.procedurestap_uri(procedurestap_base_uri)
                                self.gerelateerde_procedurestappen_uris.append(procedurestap_uri)
                                logging.info('Found related subcase {} for subcase {}'.format(procedurestap_uri, ap.procedurestap_uri(procedurestap_base_uri)))
                except AttributeError: # If vorig doc isn't an ordinary document 'dossiernummer' property doesn't exist ...
                    continue
        self.gerelateerde_procedurestappen_uris = list(set(self.gerelateerde_procedurestappen_uris))
        return self.gerelateerde_procedurestappen_uris

    def is_beslist(self):
        """
            Veld 'is beslist' bestaat niet in Doris (of wordt niet correct gebruikt).
            Men zou kunnen redeneren indien alle documenten openbaar -> beslist, maar ...
            Omwille van 'cheat' in Doris, om bv. adviezen IF af te schermen, worden deze op 'uitgesteld' gezet ...
            We gaan er dus van uit dat wanneer er een openbaar document tusssenzit (niet allemaal 'uitgesteld'), er iets beslist is
        """
        return any([doc.levenscyclus_status == 'Openbaar' for doc in self.rel_docs])

    def is_vertrouwelijk(self):
        return all([doc.confidential for doc in self.rel_docs]) and self.beslissingsfiche.confidential

    def src_uri(self, src_base_uri):
        return "{}vr/fiches/{}.{}".format(src_base_uri, self.beslissingsfiche.id, self.beslissingsfiche.mufile.extension)

    def uri(self, base_uri):
        return base_uri + "id/agendapunten/" + "{}".format(self.uuid)

    def procedurestap_uri(self, base_uri):
        return base_uri + "id/procedurestappen/" + "{}".format(self.procedurestap_uuid)

    def triples(self, ns, base_uri, src_base_uri):
        # Publicatie
        publicatie_triples = []
        for pub in self.publicaties:
            publicatie_triples += pub.triples(ns, base_uri)

        # Besluit
        besluit_uuid = str(uuid.uuid1())
        besluit_uri = URIRef(base_uri + "id/besluiten/" + "{}".format(besluit_uuid))
        besluit_triples = [
            (besluit_uri, RDF['type'], ns.BESLUIT['Besluit']),
            (besluit_uri, ns.MU['uuid'], Literal(besluit_uuid)),
            (besluit_uri, ns.DCT['source'], URIRef(self.src_uri(src_base_uri))),
        ]
        try:
            besluit_triples.append((besluit_uri, ns.BESLUITVORMING['stuknummerVR'], Literal(self.beslissingsfiche.name))) # or self.beslissingsfiche.stuknummer()
        except AttributeError:
            pass
        if self.beslissingsfiche.title:
            besluit_triples.append((besluit_uri, ns.ELI['title_short'], Literal(self.beslissingsfiche.title)))
        if self.beslissingsfiche.description:
            besluit_triples.append((besluit_uri, ns.ELI['description'], Literal(self.beslissingsfiche.description)))
        for pub in self.publicaties:
            besluit_triples.append((besluit_uri, ns.BESLUITVORMING['isGerealiseerdDoor'], URIRef(pub.uri(base_uri))))

        # Procedurestap
        procedurestap_uri = URIRef(self.procedurestap_uri(base_uri))
        procedurestap_triples = [
            (procedurestap_uri, RDF['type'], ns.DBPEDIA['UnitOfWork']),
            (procedurestap_uri, ns.MU['uuid'], Literal(self.procedurestap_uuid)),
            # (procedurestap_uri, ns.DCT['source'], URIRef(self.src_uri)),
            # (procedurestap_uri, ns.DCT['alternative'], Literal(self.beslissingsfiche)),
            # (procedurestap_uri, ns.DCT['created'], Literal(self.aanmaakdatum)),
            (procedurestap_uri, ns.BESLUITVORMING['besloten'], Literal(self.is_beslist(), datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))),
            (procedurestap_uri, ns.EXT['wordtGetoondAlsMededeling'], Literal(bool(self.type == 'MEDEDELING'), datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))),
            (procedurestap_uri, ns.EXT['procedurestapHeeftBesluit'], URIRef(self.beslissingsfiche.uri(base_uri))),
            # besluitvorming:isAangevraagdVoor via Agenda
            # besluitvorming:vertrouwelijkheid TODO, wordt een bool?
        ]
        if self.beslissingsfiche.title:
            procedurestap_triples.append((procedurestap_uri, ns.DCT['title'], Literal(self.beslissingsfiche.title))) # TODO bestaat altijd?

        for mandatee in self.beslissingsfiche.indieners:
            procedurestap_triples.append((procedurestap_uri, ns.BESLUITVORMING['heeftBevoegde'], URIRef(mandatee.uri(base_uri))))
        for rel_procedurestap_uri in self.gerelateerde_procedurestappen_uris:
            procedurestap_triples.append((procedurestap_uri, ns.DCT['relation'], URIRef(rel_procedurestap_uri)))
        for rel_doc in self.rel_docs:
            procedurestap_triples.append((procedurestap_uri, ns.EXT['bevatDocumentversie'], URIRef(rel_doc.uri(base_uri))))
        if self.news_item:
            for theme in self.news_item.themes:
                procedurestap_triples.append((procedurestap_uri, ns.DCT['subject'], URIRef(theme.uri(base_uri))))
        # besluitvorming:isGeagendeerdVia via Agendapunt
        # besluitvorming:isAangevraagdVoor -> zie Agenda
        # ext:subcaseProcedurestapFase # TODO, na aanmaken v procedurestappen de fase materializen adhv aantal in dossier? Low prio

        # Agendapunt
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.DCT['source'], URIRef(self.src_uri(src_base_uri))),
            (uri, ns.DCT['alternative'], Literal(self.beslissingsfiche.source_name)),
        ]
        procedurestap_triples.append((procedurestap_uri, ns.BESLUITVORMING['isGeagendeerdVia'], uri)) # Zie procedurestap
        if self.type in ('PUNT', 'MEDEDELING'):
            triples += [
                (uri, RDF['type'], ns.BESLUIT['Agendapunt']),
                (uri, ns.EXT['wordtGetoondAlsMededeling'], Literal(bool(self.type == 'MEDEDELING'), datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))),
            ]
        elif self.type == 'VARIA': # TODO
            triples += [
                (uri, RDF['type'], ns.BESLUIT['Agendapunt']),
                (uri, ns.EXT['wordtGetoondAlsMededeling'], Literal(True, datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))),
            ]
        triples += [
            (uri, ns.EXT['prioriteit'], Literal(self.volgnr)),
            (uri, ns.BESLUITVORMING['formeelOK'], Literal(True, datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))),
            # ext:wordtGetoondAlsMededeling see above
            # (uri, ns.EXT['heeftVerdaagd'], URIRef()), # Can't do, no data
            (uri, ns.EXT['agendapuntHeeftBesluit'], besluit_uri),
            # TODO: Confidentiality
        ]
        if self.title:
            triples.append((uri, ns.DCT['title'], Literal(self.title)))
        for mandatee in self.beslissingsfiche.indieners:
            triples.append((uri, ns.EXT['heeftBevoegdeVoorAgendapunt'], URIRef(mandatee.uri(base_uri))))
        for rel_doc in self.rel_docs:
            triples.append((uri, ns.EXT['bevatAgendapuntDocumentversie'], URIRef(rel_doc.uri(base_uri))))
        if self.news_item:
            for theme in self.news_item.themes:
                triples.append((uri, ns.EXT['agendapuntSubject'], URIRef(theme.uri(base_uri))))

        # NieuwsbriefInfo
        if self.news_item:
            triples.append((uri, ns.PROV['generated'], URIRef(self.news_item.uri(base_uri))))

        return publicatie_triples + besluit_triples + procedurestap_triples + triples
