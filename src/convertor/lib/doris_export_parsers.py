#!/usr/bin/python3

import datetime
import re

from .model.document_name import VrDocumentName, AgendaName, VrNotulenName, VrBeslissingsficheName, OcDocumentName, OcAgendaName, OcVerslagName, OcNotulenName, OcNotificatieName
from .code_lists.numbering import LATIN_ADVERBIAL_NUMERAL_2_INT
from .code_lists.governments import REGERINGEN
from .code_lists.doris import AARDEN_BESLISSING, TYPES_VERGADERING, TYPES_DOCUMENT, LEVENSCYCLUS_STATUSSEN
from .code_lists.documentum import DOCUMENTUM_TYPE_2_MIMETYPE

def p_object_id(val):
    id_match = re.match(r"^[0-9a-f]{16}$", val)
    if id_match:
        return id_match.group(0)
    else:
        raise ValueError("\"{}\" doesn't doesn't accord to the \"object_id\"-format. Should be 16 hex characters".format(val))

def p_true_false(val):
    if val == 'T':
        return True
    elif val == 'F':
        return False
    else:
        raise ValueError("\"{}\" doesn't equal \"T\" or \"F\"".format(val))

def p_keyed_dates(val):
    if val == 'nulldate':
        return None
    try:
        dates_ret = []
        keyed_dates = val.replace(',', ';').split(';')
        for k_date in keyed_dates:
            k_date = k_date.replace('-', '/').strip()
            match = re.match(r"([A-Z]|\d)?(?:(?:\s|\W)*)(\d{2}/\d{2}/\d{4})(?:(?:\s|\W)*)([A-Z]|\d)?", k_date)
            if match:
                date = datetime.datetime.strptime(match.group(2), "%d/%m/%Y").date()
                if match.group(1) or match.group(3):
                    version = match.group(1) or match.group(3)
                    try:
                        version = str(chr(version + 64))
                    except TypeError:
                        version = version if version else None
                    dates_ret.append((date, version))
            else:
                continue
        return dates_ret
    except Exception as e:
        raise e

def p_datetime(val):
    if val == 'nulldate':
        return None
    try:
        return datetime.datetime.strptime(val.strip(), "%d/%m/%Y %H:%M:%S").date()
    except Exception as e:
        raise ValueError("Invalid datetime: " + str(e))

def p_number(val):
    try:
        return int(val.strip())
    except Exception as e:
        raise ValueError("Invalid number: " + str(e))

def p_oc_session_number(val):
    try:
        return p_number(val.split('/')[-1])
    except IndexError as e:
        raise ValueError("Invalid number: " + str(e))

def p_oc_priority(val):
    match = re.match(r"^(\d+)([a-fA-F])?", val)
    if match:
        priority = int(match.group(1))
        if match.group(2):
            sub_priority = match.group(2).lower()
        else:
            sub_priority = ''
        return priority, sub_priority
    else:
        raise ValueError("Invalid oc item priority: " + str(val))

def p_ministers_old_style(val):
    """
    "Oude stijl" (tot 2004): Sannen, Byttebier, Ceysens - VM Leefmilieu, Landbouw en Ontwikkelingssamenwerking. VM Welzijn, Gezondheid en Gelijke Kansen. VM Economie, Buitenlands Beleid
    """
    if ';' in val: raise ValueError("Indieners contains ';' cannot be old-style indiener_samenvatting")
    names, many_titles = val.rsplit(' - ', 1)
    names, split_many_titles = names.split(','), many_titles.strip().strip('.').split('.')
    indieners_ret = []
    if len(names) == len(split_many_titles):
        for name, title in zip(names, split_many_titles):
            given_name, family_name = None, name.strip()
            title = title.strip()
            indieners_ret.append((given_name, family_name, title))
    elif (len(names) == 1) and (len(names) < len(split_many_titles)):
        given_name, family_name = None, names[0].strip()
        title = many_titles.strip()
        indieners_ret.append((given_name, family_name, title))
    else:
        raise ValueError("Not as many names as titles for old-style indiener_samenvatting") # Cannot be old style
    return tuple(indieners_ret)

def p_minister_new_style(indiener):
    """
    "nieuwe stijl": BOURGEOIS Geert - VM van Bestuurszaken, Buitenlands Beleid, Media en Toerisme;...
    """
    if indiener == ' - ': raise ValueError("'{}' isn't a recognized value for indiener_samenvatting".format(indiener))
    # if len(indiener.split(' - ')) > 2: raise ValueError() # Cannot be new style
    fullname, title = indiener.rsplit(' - ', 1)
    given_name_parts, family_name_parts = [], []
    hasupperpart = False
    for name_part in fullname.strip().split(' '):
        if name_part.isupper():
            hasupperpart = True
            family_name_parts.append(name_part.strip().title())
        else:
            given_name_parts.append(name_part.strip())
    if not hasupperpart:
        raise ValueError("Name doesn't contain upper case part ... can't be new style indiener")
    if family_name_parts:
        given_name, family_name = ' '.join(given_name_parts), ' '.join(family_name_parts)
    else: # If only camel case words in full name, we assume no given name was written
        given_name, family_name = None, ' '.join(given_name_parts)
    if title.strip():
        title = title.strip()
    else:
        title = None
    return given_name.strip(), family_name.strip(), title.strip()

def p_indiener_samenvatting(val):
    # val = re.sub(r'\s{2,}', ' ', val).strip()
    val = val.strip()
    if not val:
        raise ValueError("Empty string isn't a recognized value for indiener_samenvatting")
    parsed_indieners = []
    indieners = val.split(';')
    for indiener in indieners:
        if '-' in indiener:
            try:
                parsed_indieners.append(p_minister_new_style(indiener))
            except Exception as e:
                try:
                    parsed_indieners += p_ministers_old_style(indiener)
                except Exception as e:
                    # import pdb; pdb.set_trace()
                    if len(indieners) == 1:
                        raise e
                    else:
                        continue
            # parsed_indieners.append(indiener)
        else:
            parsed_indieners += list(map(str.strip, indiener.replace('/', ';').replace('.', ';').replace(',', ';').replace(':', ';').split(';')))
    return parsed_indieners

def p_aard(val):
    for aard in AARDEN_BESLISSING:
        if val.lower() == aard.lower():
            return aard
    raise ValueError("{} isn't a valid value for aard van beslissing".format(val))

def p_verg_type(val):
    for type in TYPES_VERGADERING:
        if val.lower() == type.lower():
            return type
    raise ValueError("{} isn't a valid value for type vergadering".format(val))

def p_doc_type(val):
    for type in TYPES_DOCUMENT:
        if val.lower() == type.lower():
            return type
    raise ValueError("{} isn't a valid value for type document".format(val))

def p_lifecycle_state(val):
    if val in LEVENSCYCLUS_STATUSSEN:
        return val
    raise ValueError("{} isn't a valid value for levenscyclus_status".format(val))

def p_keywords(val):
    keywords = val.replace(' ', ',').replace(';', ',').split(',')
    return tuple([kw.strip() for kw in keywords if bool(kw.strip()) is True])

def p_doc_name(val):
    def p_ordinary_doc(val):
        """ VR 2008 2305 MED.0223 """
        docname_match = re.match(r"(V[Rr]|VE)( |\/)(\d{4})( |\/)(\d{2})(\d{2})( |\/)(DOC|DEC|MED|VAR)\.(\d{2,4})(\/\d+)?([A-Z]{3,})?$", val)
        if not docname_match:
            raise ValueError('\'{}\' isn\'t a valid ordinary document name'.format(val))
        context = docname_match.group(1).upper()
        year = int(docname_match.group(3))
        day = int(docname_match.group(5))
        month = int(docname_match.group(6))
        type = docname_match.group(8)
        dossier_nr = int(docname_match.group(9))
        doc_nr = int(docname_match.group(10).strip('/')) if docname_match.group(10) else None
        if docname_match.group(11):
            version_like = docname_match.group(11).lower()
            if version_like in LATIN_ADVERBIAL_NUMERAL_2_INT.keys():
                version = LATIN_ADVERBIAL_NUMERAL_2_INT[version_like]
            else:
                raise ValueError('\'{}\' looks like a sub-version of a document name but isn\'t'.format(version_like))
        else:
            version = 1
        date = datetime.date(year, month, day)
        return VrDocumentName(context, date, dossier_nr, type, doc_nr), version

    def p_agenda(val):
        """ VR AGENDA 20021122 """
        docname_match = re.match(r"(V[Rr]|VE|OC) AGENDA (\d{4})(\d{2})(\d{2})", val)
        if not docname_match:
            raise ValueError('\'{}\' isn\'t a valid agenda document name'.format(val))
        context = docname_match.group(1).upper()
        year = int(docname_match.group(2))
        month = int(docname_match.group(3))
        day = int(docname_match.group(4))
        date = datetime.date(year, month, day)
        return AgendaName(context, date)

    def p_notulen(val):
        """ VR PV 2000/12BIS """
        docname_match = re.match(r"(V[Rr]|VE) PV (\d{4})\/(\d+)([A-Z]{3,})?", val)
        if not docname_match:
            raise ValueError('\'{}\' isn\'t a valid notulen document name'.format(val))
        context = docname_match.group(1).upper()
        year = int(docname_match.group(2))
        verg_nummer = int(docname_match.group(3))
        if docname_match.group(4):
            version_like = docname_match.group(4).lower()
            if version_like in LATIN_ADVERBIAL_NUMERAL_2_INT.keys():
                version = LATIN_ADVERBIAL_NUMERAL_2_INT[version_like]
            else:
                raise ValueError('\'{}\' looks like a sub-version of a document name but isn\'t'.format(version_like))
        else:
            version = 1
        return VrNotulenName(context, year, verg_nummer), version

    try:
        return p_ordinary_doc(val)
    except ValueError as e:
        pass
    try:
        return p_agenda(val)
    except ValueError as e:
        pass
    try:
        return p_notulen(val)
    except ValueError as e:
        pass
    raise ValueError("{} isn't a recognized value for doc_name".format(val))

def p_oc_doc_name(val):
    def p_ordinary_doc(val):
        """
        "OC 20181107 PUNT 03"
        "OC 20181107 PUNT 04"
        "OC 20181107 PUNT 05A"
        "OC 20181107 PUNT 05ABIS"
        """
        docname_match = re.match(r"OC (\d{4})(\d{2})(\d{2}) PUNT (\d{2})(?:([A-Z])|((?:[A-Z]){3,}))?$", val)
        if not docname_match:
            raise ValueError('\'{}\' isn\'t a valid ordinary document name'.format(val))
        year = int(docname_match.group(1))
        month = int(docname_match.group(2))
        day = int(docname_match.group(3))
        date = datetime.date(year, month, day)
        punt_nr = int(docname_match.group(4))
        if docname_match.group(5):
            doc_nr = ord(docname_match.group(5).lower()) - 96
            version = None
        elif docname_match.group(6):
            version_like = docname_match.group(6).lower()
            if version_like in LATIN_ADVERBIAL_NUMERAL_2_INT.keys():
                version = LATIN_ADVERBIAL_NUMERAL_2_INT[version_like]
                doc_nr = None
            else:
                try:
                    version = LATIN_ADVERBIAL_NUMERAL_2_INT[version_like[1:]]
                except KeyError:
                    raise ValueError("'{}' isn't a valid latin adverbial numeral for versioning".format(version_like[1:]))
                doc_nr = ord(version_like[0]) - 96
        else:
            version = None
            doc_nr = None
        return OcDocumentName(date, punt_nr, doc_nr), version

    def p_agenda(val):
        """ OC 20021122 AGENDA """
        docname_match = re.match(r"OC (\d{4})(\d{2})(\d{2}) AGENDA$", val)
        if not docname_match:
            raise ValueError('\'{}\' isn\'t a valid agenda document name'.format(val))
        year = int(docname_match.group(1))
        month = int(docname_match.group(2))
        day = int(docname_match.group(3))
        date = datetime.date(year, month, day)
        return OcAgendaName(date)

    def p_verslag(val):
        """ OC 20021122 VERSLAG """
        docname_match = re.match(r"OC (\d{4})(\d{2})(\d{2}) VERSLAG$", val)
        if not docname_match:
            raise ValueError('\'{}\' isn\'t a valid verslag document name'.format(val))
        year = int(docname_match.group(1))
        month = int(docname_match.group(2))
        day = int(docname_match.group(3))
        date = datetime.date(year, month, day)
        return OcVerslagName(date)

    def p_notulen(val):
        """
            OC 20051116 PV 13
            OC 20170220 NOTULEN
        """
        docname_match = re.match(r"OC (\d{4})(\d{2})(\d{2}) (?:(?:NOTULEN)|(?:PV (?:\d+\/)?(\d+)))$", val)
        if not docname_match:
            raise ValueError('\'{}\' isn\'t a valid notulen document name'.format(val))
        year = int(docname_match.group(1))
        month = int(docname_match.group(2))
        day = int(docname_match.group(3))
        date = datetime.date(year, month, day)
        if docname_match.group(4):
            zitting_nr = int(docname_match.group(4))
        else:
            zitting_nr = None
        return OcNotulenName(date, zitting_nr)
    
    val = val.strip().upper()
    try:
        return p_ordinary_doc(val)
    except ValueError as e:
        pass
    try:
        return p_agenda(val)
    except ValueError as e:
        pass
    try:
        return p_verslag(val)
    except ValueError as e:
        pass
    try:
        return p_notulen(val)
    except ValueError as e:
        pass
    # import pdb; pdb.set_trace()
    raise ValueError("{} isn't a recognized value for doc_name".format(val))


def p_agendapunt_name(val):
    """
    VR/PV/1984/38 - PUNT 16
    VR PV 2000/52 - MEDEDELING 0008
    """
    agendapunt_match = re.match(r"(OC|VR)( |\/)(PV)( |\/)(\d{4})\/(\d{1,3})( - | )(PUNT|MEDEDELING|VARIA|MED|VAR)( )?((?:\d)*)(BIS|TER|QUATER)?", val)
    if not agendapunt_match:
        raise ValueError("'{}' isn't a valid beslissingsfiche name".format(val))
    context = agendapunt_match.group(1)
    pv = agendapunt_match.group(3)
    year = int(agendapunt_match.group(5))
    verg_nummer = int(agendapunt_match.group(6))
    type = agendapunt_match.group(8)
    if type == 'MED': # CLEANING
        type = 'MEDEDELING'
    elif type == 'VAR':
        type = 'VARIA'
    if agendapunt_match.group(10):
        number = int(agendapunt_match.group(10).strip())
    else:
        number = None
    if agendapunt_match.group(11):
        version = LATIN_ADVERBIAL_NUMERAL_2_INT[agendapunt_match.group(11).lower()]
    else:
        version = None
    return VrBeslissingsficheName(context, year, verg_nummer, number, type), version

def p_oc_notificatie_name(val):
    """ OC 20060906 NOT PT 04 """
    agendapunt_match = re.match(r"OC (\d{4})(\d{2})(\d{2}) NOT PT (\d{2})", val)
    if not agendapunt_match:
        raise ValueError("'{}' isn't a valid notification name".format(val))
    year = int(agendapunt_match.group(1))
    month = int(agendapunt_match.group(2))
    day = int(agendapunt_match.group(3))
    date = datetime.date(year, month, day)
    number = int(agendapunt_match.group(4).strip())
    return OcNotificatieName(date, number)

def p_oc_fed_case_name(val):
    """ 2016C96610.001 """
    doc_matches = re.finditer(r"(\()?(\d{4}[A-Z]\d{5}\.\d{3})(\))?", val)
    names = []
    for doc_match in doc_matches:
        doc_name = doc_match.group(2)
        betweenbrackets = bool(doc_match.group(1) and doc_match.group(3))
        names.append(tuple([doc_name, betweenbrackets]))
    return names

def p_doc_list(val):
    if not val:
        return tuple()
    else:
        return tuple([doc_name.strip() for doc_name in val.replace(',', ';').split(';')])


def p_content_type(val):
    if val in DOCUMENTUM_TYPE_2_MIMETYPE:
        return (val, DOCUMENTUM_TYPE_2_MIMETYPE[val])
    else:
        raise ValueError('Unknown Documentum content_type \'{}\''.format(val))
