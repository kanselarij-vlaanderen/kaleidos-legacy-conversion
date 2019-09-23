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
    return find(agenda_documenten, lambda doc: doc.parsed_name.datum == date and doc._zittingnr == verg_nr)

def find_notulen_document(notulen_documenten, date, zittingnr):
    return find(notulen_documenten, lambda doc: doc.parsed_name.jaar == date.year and doc._zittingnr == zittingnr)

def find_oc_notulen_document(notulen_documenten, date, zittingnr):
    return find(notulen_documenten, lambda doc: doc.parsed_name.datum == date and (doc._zittingnr == zittingnr if doc._zittingnr else True))

class Agenda:
    """docstring for Agenda."""
    def __init__(self, datum, zittingnr):
        super().__init__()
        self.uuid = str(uuid.uuid1())

        self.zitting_uuid = str(uuid.uuid1())
        self.notulen_uuid = str(uuid.uuid1())
        self.datum = datum
        self.zittingnr = zittingnr
        self.type_ref = None

        self.agendapunten = []
        self.notulen = None
        self.agenda_doc = None

        self.geplande_start = TIMEZONE.localize(datetime.datetime.combine(self.datum, datetime.time(12, 0, 0)))
        
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
        retval += "\n\n\tNotulen document:\n"
        if self.notulen:
            retval += textwrap.indent(str(self.notulen) + '\n', '\t\t')
        retval += "\n\n\tAgenda document:\n"
        if self.agenda_doc:
            retval += textwrap.indent(str(self.agenda_doc) + '\n', '\t\t')

        return retval

    @property
    def punten(self):
        return sorted(filter(lambda p: not p.is_announcement, self.agendapunten), key=lambda p: p.volgnr if p.volgnr else 0)

    @property
    def mededelingen(self):
        return sorted(filter(lambda p: p.is_announcement, self.agendapunten), key=lambda p: p.volgnr if p.volgnr else 0)

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

    def link_news_items(self, news_item_lut):
        if (self.datum.year, self.zittingnr) in news_item_lut:
            nis = news_item_lut[(self.datum.year, self.zittingnr)]
        elif self.datum in news_item_lut: # Old news item records without session number
            nis = news_item_lut[self.datum]
        else:
            logging.warning("No newsletter available for agenda {} - {}".format(self.datum, self.zittingnr))
            return
        for ni in nis:
            for item in self.agendapunten:
                if ni.agenda_item_nr == item.volgnr:
                    if (item.is_announcement and ni.agenda_item_type == 'MEDEDELING') or \
                        (not item.is_announcement and ni.agenda_item_type == 'PUNT'):
                        item.news_item = ni

    def uri(self, base_uri):
        return base_uri + "id/agendas/" + "{}".format(self.uuid)

    def zitting_uri(self, base_uri):
        return base_uri + "id/zittingen/" + "{}".format(self.zitting_uuid)

    def notulen_uri(self, base_uri):
        return base_uri + "id/notulen/" + "{}".format(self.notulen_uuid)

    def triples(self, ns, base_uri): # DONE, except varia
        # Agenda
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.BESLUITVORMING['Agenda']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.EXT['finaleVersie'], Literal('true', datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))),
            (uri, ns.EXT['agendaNaam'], Literal('')),
            (uri, ns.EXT['accepted'], Literal('true', datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))),
            (uri, ns.BESLUIT['isAangemaaktVoor'], URIRef(self.zitting_uri(base_uri))),
        ]

        # Zitting
        zitting_uri = URIRef(self.zitting_uri(base_uri))
        zitting_triples = [
            (zitting_uri, RDF['type'], ns.BESLUIT['Zitting']),
            (zitting_uri, ns.MU['uuid'], Literal(self.zitting_uuid)),
            (zitting_uri, ns.DCT['source'], URIRef(self.uri(base_uri))),
            (zitting_uri, ns.BESLUIT['geplandeStart'], Literal(self.geplande_start.isoformat(), datatype=XSD.dateTime)),
            # (zitting_uri, ns.PROV['startedAtTime'], Literal()),
            # (zitting_uri, ns.PROV['endedAtTime'], Literal()),
            (zitting_uri, ns.ADMS['identifier'], Literal(self.zittingnr)),
            (zitting_uri, ns.EXT['finaleZittingVersie'], Literal(True, datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))),
            (zitting_uri, ns.BESLUITVORMING['behandelt'], uri)
        ]

        # Agenda & Zitting
        for punt in self.agendapunten:
            zitting_triples.append((zitting_uri, ns.BESLUITVORMING['isAangevraagdVoor'], URIRef(punt.procedurestap_uri(base_uri))))
            triples.append((uri, ns.DCT['hasPart'], URIRef(punt.uri(base_uri))))
            
        if self.notulen:
            # Notulen
            notulen_uri = URIRef(self.notulen_uri(base_uri))
            notulen_triples = [
                (notulen_uri, RDF['type'], ns.EXT['Notule']),
                (notulen_uri, ns.MU['uuid'], Literal(self.notulen_uuid)),
                # (notulen_uri, ns.EXT['aangemaaktOp'], ),
                # (notulen_uri, ns.EXT['description'], ),
                (zitting_uri, ns.EXT['algemeneNotulen'], notulen_uri),
                (notulen_uri, ns.EXT['getekendeDocumentVersiesVoorNotulen'], URIRef(self.notulen.uri(base_uri)))
            ]
        else:
            notulen_triples = []
        if self.agenda_doc:
            # Agenda document
            agenda_triples = [
                (zitting_uri, ns.EXT['zittingDocumentversie'], URIRef(self.agenda_doc.uri(base_uri)))
            ]
        else:
            agenda_triples = []
        return triples + zitting_triples + notulen_triples + agenda_triples


class Agendapunt():
    """docstring for Agendapunt."""
    def __init__(self, volgnr=None, beslissingsfiche=None):
        super().__init__()
        self.uuid = str(uuid.uuid1())
        self.src_uri = ''
        self.procedurestap_uuid = str(uuid.uuid1())
        self.volgnr = volgnr

        self.zitting = None
        self.besl_vereist = None

        self.beslissingsfiche = beslissingsfiche # doc version
        self.beslissingsfiche_doc = None
        self.documents = [] # All document versions related to the agenda item
        self.decision_documents = [] # Document versions related to the decision of this agenda item

        self.news_item = None

        self.gerelateerde_procedurestappen_uris = []

    def __str__(self):
        return '{}{} ({}/{})'.format('Mededeling' if self.is_announcement else 'Punt', ' ' + str(self.volgnr) if self.volgnr else '', len(self.decision_documents), len(self.documents))

    @property
    def title(self):
        if self.beslissingsfiche:
            title = self.beslissingsfiche.title
            if self.beslissingsfiche.parsed_name.punt_type == 'VARIA':
                if title:
                    title = 'VARIA: ' + title
                else:
                    title = 'VARIA'
            return title
        else:
            try:
                return self.documents[0].title
            except IndexError:
                return ''

    @property
    def short_title(self):
        if self.beslissingsfiche:
            return self.beslissingsfiche.short_title
        else:
            try:
                return self.documents[0].short_title
            except IndexError:
                return ''

    @property
    def is_announcement(self):
        return (not self.beslissingsfiche) or (self.beslissingsfiche.parsed_name.punt_type in ('MEDEDELING', 'VARIA'))
        
    @property
    def has_decision(self):
        return bool(self.beslissingsfiche)

    @property
    def confidential(self):
        return all([doc.confidential for doc in self.decision_documents]) and self.beslissingsfiche.confidential
        
    def link_document_refs(self, doc_lut, fallback_doc_lut):
        if self.beslissingsfiche and self.beslissingsfiche._decision_doc_refs:
            self.decision_documents = []
            for rel_doc in self.beslissingsfiche._decision_doc_refs:
                try:
                    doc = doc_lut[rel_doc['source']][0] # WARNING: As value for doc_lut key is a tuple of docs (because of ambiguity), only take the first one
                    self.decision_documents.append(doc)
                    if doc not in self.documents:
                        self.documents.append(doc)
                except KeyError as e:
                    try:
                        logging.info("No match found by literal 'dar_rel_docs'-key {}, trying search by properties".format(rel_doc['source']))
                        if rel_doc['success']:
                            doc = fallback_doc_lut[rel_doc['parsed']][0] # WARNING: As value for doc_lut key is a tuple of docs (because of ambiguity), only take the first one
                            self.decision_documents.append(doc)
                            if doc not in self.documents:
                                self.documents.append(doc)
                        else:
                            logging.warning("Related doc {} doesn't have a parsed name".format(rel_doc['source']))
                    except KeyError as e:
                        logging.warning("No match found for 'related' doc {}".format(rel_doc['source']))
        return self.decision_documents

    def has_decision_content(self):
        """
            Veld 'is beslist' bestaat niet in Doris (of wordt niet correct gebruikt).
            Men zou kunnen redeneren indien alle documenten openbaar -> beslist, maar ...
            Omwille van 'cheat' in Doris, om bv. adviezen IF af te schermen, worden deze op 'uitgesteld' gezet ...
            We gaan er dus van uit dat wanneer er een openbaar document tusssenzit (niet allemaal 'uitgesteld'), er iets beslist is
        """
        return self.decision_documents and any([doc.levenscyclus_status == 'Openbaar' for doc in self.decision_documents])

    def uri(self, base_uri):
        if self.has_decision:
            return base_uri + "id/agendapunten/" + "{}".format(self.uuid)
        else:
            return base_uri + "id/mededelingen/" + "{}".format(self.uuid)

    def procedurestap_uri(self, base_uri):
        return base_uri + "id/procedurestappen/" + "{}".format(self.procedurestap_uuid)

    def triples(self, ns, base_uri):
        # Agendapunt
        uri = URIRef(self.uri(base_uri))
        triples = [
            (uri, RDF['type'], ns.BESLUIT['Agendapunt']),
            (uri, ns.MU['uuid'], Literal(self.uuid)),
            (uri, ns.DCT['source'], URIRef(self.src_uri)),
            (uri, ns.EXT['prioriteit'], Literal(self.volgnr)),
        ]
        if self.short_title:
            triples.append((uri, ns.DCT['alternative'], Literal(self.short_title)))
        if self.title:
            triples.append((uri, ns.DCT['title'], Literal(self.title)))
        if self.news_item:
            for theme in self.news_item.themes:
                triples.append((uri, ns.EXT['agendapuntSubject'], URIRef(theme.uri(base_uri))))
        for doc in self.documents:
            triples.append((uri,
                            ns.EXT['bevatAgendapuntDocumentversie'],
                            URIRef(doc.uri(base_uri))))
        if self.is_announcement:
            triples.append((uri,
                            ns.EXT['wordtGetoondAlsMededeling'],
                            Literal('true', datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))))
        else:
            triples.append((uri,
                            ns.EXT['wordtGetoondAlsMededeling'],
                            Literal('false', datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))))
            triples.append((uri, RDF['type'], ns.BESLUITVORMING['Mededeling'])) # Subtype

        if self.has_decision: # Agenda item with decision
            # Besluit
            besluit_uuid = str(uuid.uuid1())
            besluit_uri = URIRef(base_uri + "id/besluiten/" + "{}".format(besluit_uuid))
            besluit_triples = [
                (besluit_uri, RDF['type'], ns.BESLUIT['Besluit']),
                (besluit_uri, ns.MU['uuid'], Literal(besluit_uuid)),
                (besluit_uri, ns.DCT['source'], URIRef(self.src_uri)),
                (besluit_uri, ns.BESLUITVORMING['goedgekeurd'], Literal('true' if self.has_decision_content() else 'false', datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))),
                (besluit_uri, ns.EXT['beslissingsfiche'], URIRef(self.beslissingsfiche.document.uri(base_uri))),
            ]
            if self.short_title:
                besluit_triples.append((besluit_uri, ns.ELI['title_short'], Literal(self.short_title)))
            for doc in self.decision_documents:
                triples += [
                    (besluit_uri, ns.EXT['documentenVoorBeslissing'], URIRef(doc.uri(base_uri)))
                ]
            
            # Procedurestap
            procedurestap_uri = URIRef(self.procedurestap_uri(base_uri))
            triples += [
                (procedurestap_uri, RDF['type'], ns.DBPEDIA['UnitOfWork']),
                (procedurestap_uri, ns.MU['uuid'], Literal(self.procedurestap_uuid)),
                (procedurestap_uri, ns.DCT['source'], URIRef(self.src_uri)),
                (procedurestap_uri, ns.DCT['created'], Literal(self.zitting.geplande_start.isoformat(), datatype=XSD.dateTime)), # For sorting i new app
                (procedurestap_uri, ns.EXT['modified'], Literal(self.zitting.geplande_start.isoformat(), datatype=XSD.dateTime)),
                (procedurestap_uri, ns.BESLUITVORMING['isGeagendeerdVia'], uri),
                (procedurestap_uri, ns.EXT['procedurestapHeeftBesluit'], URIRef(besluit_uri)),
                (procedurestap_uri,
                 ns.EXT['wordtGetoondAlsMededeling'],
                 Literal('true' if self.is_announcement else 'false', datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean')))
            ]
            if self.news_item:
                triples.append((procedurestap_uri, ns.PROV['generated'], URIRef(self.news_item.uri(base_uri))))
            for doc in self.documents:
                triples.append((procedurestap_uri,
                                ns.EXT['bevatDocumentversie'],
                                URIRef(doc.uri(base_uri))))
            # for rel_procedurestap_uri in self.gerelateerde_procedurestappen_uris:
            #     triples.append((procedurestap_uri, ns.DCT['relation'], URIRef(rel_procedurestap_uri)))

            # Procedurestap
            procedurestap_uri = URIRef(self.procedurestap_uri(base_uri))
            triples += [
                # (uri, ns.BESLUITVORMING['formeelOK'], Literal('true', datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))),
                # (procedurestap_uri, ns.BESLUITVORMING['formeelOK'], Literal('true', datatype=URIRef('http://mu.semte.ch/vocabularies/typed-literals/boolean'))),
                # besluitvorming:isAangevraagdVoor via Agenda
                # besluitvorming:vertrouwelijkheid TODO, wordt een bool?
            ]
            if self.short_title:
                triples.append((procedurestap_uri, 
                                ns.DCT['alternative'],
                                Literal(self.short_title)))
            if self.title:
                triples.append((procedurestap_uri,
                                ns.DCT['title'],
                                Literal(self.title)))
            if self.news_item:
                for theme in self.news_item.themes:
                    triples.append((procedurestap_uri,
                                    ns.DCT['subject'],
                                    URIRef(theme.uri(base_uri))))
            for mandatee in self.beslissingsfiche.indieners:
                triples.append((procedurestap_uri,
                                ns.BESLUITVORMING['heeftBevoegde'],
                                URIRef(mandatee.uri(base_uri))))
            # ext:subcaseProcedurestapFase # TODO, na aanmaken v procedurestappen de fase materializen adhv aantal in dossier? Low prio
            triples += besluit_triples
        else:
            try:
                submitters = next(filter(lambda d: d.indieners is not [], self.documents)).indieners
                for mandatee in submitters:
                    triples.append((uri,
                                    ns.EXT['heeftIndiener'],
                                    URIRef(mandatee.uri(base_uri))))
            except StopIteration:
                pass # No submitters

        return triples
