#!/usr/bin/python3
import itertools
import json
import logging

from .model.mandatee import Mandatee, Person
from .model.governing_body import GoverningBody

def load_submitter_mapping(path):
    with open(path, mode='r') as f:
        uuids_by_id = json.load(f)
    return uuids_by_id

def search_person(persons, family_name, given_name):
    try:
        return next(person for person in persons if person.given_name == given_name and person.family_name == family_name)
    except StopIteration:
        pass

def find_administration(administrations, date):
    for gov in administrations:
        if date > gov.installation_date:
            if gov.resignation_date:
                if date < gov.resignation_date:
                    return gov
                continue
            else:
                return gov
        continue
    return None

def search_mandatee(mandatees, person, start_date, official_title):
    for mtee in mandatees:
        if mtee.person == person and mtee.start_date == start_date and mtee.official_title == official_title:
            return mtee
        continue
    return None

def create_submitters_by_ref(agendas, administrations, submitter_uuid_lut):
    submitters_by_ref = {}
    governing_bodies = []
    persons = []
    mandatees = []
    for agenda in reversed(agendas): # From most recent to older (most recent have more given names, avoid wrong coalescing based on family name)
        date = agenda.datum
        gov = find_administration(administrations, date)
        if not gov:
            logging.warning("No active government found on {}".format(date))
            continue
        for agendapunt in agenda.agendapunten:
            rel_docs = agendapunt.documents + [agendapunt.beslissingsfiche] if agendapunt.beslissingsfiche else []
            for rel_doc in rel_docs:
                submitter_refs = rel_doc._indiener_refs
                for submitter in submitter_refs:
                    if (str(submitter) in submitters_by_ref) or (str(submitter)+gov.uuid in submitters_by_ref):
                        continue
                    if isinstance(submitter, tuple): # A mandatee
                        ref = str(submitter) + gov.uuid
                        given_name, family_name, title = submitter
                        person = search_person(persons, family_name, given_name)
                        if not person:
                            person = Person(family_name, given_name)
                            person.src_uri = rel_doc.src_uri
                            persons.append(person)
                        mandatee = search_mandatee(mandatees, person, gov.installation_date, title)
                        if not mandatee:
                            mandatee = Mandatee(person, gov.installation_date)
                            if ref in submitter_uuid_lut:
                                mandatee.uuid = submitter_uuid_lut[ref]
                            else:
                                mandatee.deprecated = True
                            mandatee.src_uri = rel_doc.src_uri
                            mandatees.append(mandatee)
                            gov.mandatees.append(mandatee)
                            gov.mandatees.sort(key=lambda m: tuple((m.start_date, m.person.family_name)))
                            mandatee.official_title = title
                            mandatee.end_date = gov.resignation_date
                            mandatee.mandate_uri = gov.minister_mandate_uri # We assume all ministers. Differentiation MP, vMP in postprocessing
                        submitters_by_ref[ref] = mandatee
                    elif isinstance(submitter, str): # A governing organ
                        ref = submitter
                        governing_body = GoverningBody(submitter)
                        if ref in submitter_uuid_lut:
                            governing_body.uuid = submitter_uuid_lut[ref]
                        else:
                            governing_body.deprecated = True
                        governing_bodies.append(governing_body)
                        submitters_by_ref[ref] = governing_body
                    else:
                        logging.warning('Unexpected submitter reference type {}'.format(type(submitter)))
                        continue
    return submitters_by_ref, persons

def mandatees_by_period_by_src(mandatees):
    mandatees_by_period_by_src = {}
    mandatees = sorted(mandatees, key=lambda m: (m.start_date, m.end_date, m.person))
    for k, g in itertools.groupby(mandatees, lambda m: (m.start_date, m.end_date, m.person)):
        mandatee = tuple(g)[0]
        mandatees_by_period_by_src[(mandatee.start_date, mandatee.end_date, mandatee.source)] = mandatee
        if len(tuple(g)) > 1:
            logging.warning('More than 1 instance of seemingly unique mandatee found {}'.format(tuple(g)))
    return mandatees_by_period_by_src

