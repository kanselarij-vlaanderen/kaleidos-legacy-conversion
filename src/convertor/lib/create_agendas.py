#!/usr/bin/python3
import logging

from .model.agenda import Agenda
from .search import find_agenda

# Create agendas with item structure out of fiches
def create_agendas(agendapunten):
    agendas = []
    for agendapunt in agendapunten:
        agenda = find_agenda(agendas, agendapunt.beslissingsfiche.zittingdatum, agendapunt.beslissingsfiche.zittingnr)
        if not agenda:
            try:
                agenda = create_agenda(agendapunt.beslissingsfiche.zittingdatum, agendapunt.beslissingsfiche.zittingnr)
            except ValueError as e:
                logging.warning(str(e))
                continue
            agendas.append(agenda)

        agenda.agendapunten.append(agendapunt)

    # Sort agendas by date and materialize references to documents
    agendas.sort(key=lambda a: tuple((a.datum.year, a.zittingnr)))

    return agendas

def create_agenda(zittingdatum, zittingnr):
    if not zittingdatum:
        raise ValueError("No zittingdatum {}, skipping agenda creation ...".format(zittingdatum))
    if not zittingnr:
        raise ValueError("No zittingnr {}, skipping agenda creation ...".format(zittingnr))
    return Agenda(zittingdatum, zittingnr)
