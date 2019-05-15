#!/usr/bin/python3

# From nieuwsberichten db
BELEIDSVELDEN = (
    'Begroting',
    'Financiën',
    'Energie',
    'Werk',
    'Economie',
    'Innovatie',
    'Sport',
    'Binnenlands Bestuur',
    'Inburgering',
    'Wonen',
    'Gelijke Kansen en Armoedebestrijding',
    'Buitenlands Beleid',
    'Onroerend Erfgoed',
    'Cultuur',
    'Media',
    'Jeugd',
    'Brussel',
    'Mobiliteit',
    'Openbare Werken',
    'Vlaamse Rand',
    'Toerisme',
    'Dierenwelzijn',
    'Onderwijs',
    ''
)

MANDATARIS_TYPES = (
    'Minister',
    'Viceminister-President',
    'Minister-President',
)

MANDATARIS_TYPES_BY_EDITORIAL_TITLE_KEY = {
    1: (MANDATARIS_TYPES[0]), # minister van ... / Vlaams minister van ...
    2: (MANDATARIS_TYPES[0], MANDATARIS_TYPES[1]), # minister vice-president, ... / minister vice-president van ...
    5: (MANDATARIS_TYPES[0], MANDATARIS_TYPES[1]), # viceminister-president van de Vlaamse Regering en Vlaams minister ...
    3: (MANDATARIS_TYPES[0], MANDATARIS_TYPES[2]), # Minister-president, ... / minister-president van de Vlaamse Regering en Vlaams minister ...
}