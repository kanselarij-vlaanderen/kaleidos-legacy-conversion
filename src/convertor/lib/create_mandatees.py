#!/usr/bin/python3
import itertools
import logging

from .model.mandatee import Mandatee, Person, Mandate

def search_person(persons, family_name, given_name=None):
    if given_name:
        try:
            return next(person for person in persons if person.given_name == given_name and person.family_name == family_name)
        except StopIteration:
            pass
    try:
        return next(person for person in persons if person.family_name == family_name)
    except StopIteration:
        return None

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

def search_mandatee(mandatees, person, start_date, official_title):
    for mtee in mandatees:
        if mtee.person == person and mtee.start_date == start_date and mtee.official_title == official_title:
            return mtee
        continue
    return None

def create_persons_mandatees_mandates(agendas, governments):
    persons = []
    mandatees = []
    mandates = []
    for agenda in agendas:
        date = agenda.datum
        gov = search_government(governments, date)
        if not gov:
            logging.warning("No active government found on {}".format(date))
            continue
        for agendapunt in agenda.agendapunten:
            for rel_doc in [agendapunt.beslissingsfiche] + agendapunt.rel_docs:
                indiener_refs = filter(lambda ref: isinstance(ref, tuple), rel_doc._indiener_refs)
                for indiener in indiener_refs:
                    given_name, family_name, title = indiener
                    person = search_person(persons, family_name, given_name)
                    if not person:
                        person = Person(family_name, given_name)
                        person.src_uri = rel_doc.src_uri
                        persons.append(person)
                    elif (not person.given_name) and given_name:
                        person.given_name = given_name
                        person.src_uri = rel_doc.src_uri
                    mandatee = search_mandatee(mandatees, person, gov.installation_date, title)
                    if not mandatee:
                        mandatee = Mandatee(person, gov.installation_date)
                        mandatee.src_uri = rel_doc.src_uri
                        mandatees.append(mandatee)
                        gov.mandatees.append(mandatee)
                        gov.mandatees.sort(key=lambda m: tuple((m.start_date, m.person.family_name)))
                        mandatee.official_title = title
                        mandatee.end_date = gov.resignation_date
                        mandatee.source = indiener
                        mandatee.src_uri = agendapunt.uri
    return persons, mandatees, mandates

def mandatees_by_period_by_src(mandatees):
    mandatees_by_period_by_src = {}
    for k, g in itertools.groupby(mandatees, lambda m: (m.start_date, m.end_date, m.person)):
        mandatee = tuple(g)[0]
        mandatees_by_period_by_src[(mandatee.start_date, mandatee.end_date, mandatee.source)] = mandatee
        if len(tuple(g)) > 1:
            logging.warning('More than 1 instance of seemingly unique mandatee found {}'.format(tuple(g)))
    return mandatees_by_period_by_src

