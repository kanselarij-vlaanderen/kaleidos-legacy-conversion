#!/usr/bin/python3

import logging

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
    return find(agenda_documenten, lambda doc: doc.datum == date and doc.zittingnr == verg_nr)

def find_notulen_document(notulen_documenten, date, zittingnr):
    return find(notulen_documenten, lambda doc: doc.jaar == date.year and doc.zittingnr == zittingnr)
