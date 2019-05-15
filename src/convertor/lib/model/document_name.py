#!/usr/bin/python3
from lib.code_lists.numbering import INT_2_LATIN_ADVERBIAL_NUMERAL

# abstract base class
class DocumentName:
    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.name()

    def name(self):
        raise NotImplementedError("Please Implement this method")

class VersionedDocumentName(DocumentName):
    def __init__(self):
        super().__init__()

    def versioned_name(self, versie_nr=None):
        versie_str = INT_2_LATIN_ADVERBIAL_NUMERAL[versie_nr].upper() if versie_nr and (versie_nr > 1) else ''
        return self.name() + versie_str

class VrDocumentName(VersionedDocumentName):
    """docstring for DocumentVersion."""
    def __init__(self, context, datum, dossier_nr, doc_type='DOC', doc_nr=None):
        assert context in ('VE', 'VR')
        assert doc_type in ('DOC', 'MED', 'VAR')
        super().__init__()
        self.context = context
        self.datum = datum
        self.dossier_nr = dossier_nr
        self.doc_type = doc_type
        self.doc_nr = doc_nr

    def name(self):
        """ VR 2008 2305 MED.0223 """
        doc_nr_str = '/' + str(self.doc_nr) if self.doc_nr else ''
        return '{} {} {:02d}{:02d} {}.{:04d}{}'.format(self.context,
                                                       self.datum.year,
                                                       self.datum.day,
                                                       self.datum.month,
                                                       self.doc_type.upper(),
                                                       self.dossier_nr,
                                                       doc_nr_str)

class OcDocumentName(VersionedDocumentName):
    """docstring for DocumentVersion."""
    def __init__(self, context, datum, punt_nr, punt_type='DOC', doc_nr=None):
        assert context in ('OC')
        assert punt_type in ('PUNT', 'MEDEDELING', 'VARIA')
        super().__init__()
        self.context = context
        self.datum = datum
        self.punt_nr = punt_nr
        self.punt_type = punt_type
        self.doc_nr = doc_nr

    def name(self):
        """
        "OC 20181107 PUNT 03"
        "OC 20181107 PUNT 04"
        "OC 20181107 PUNT 05A"
        "OC 20181107 PUNT 05ABIS"
        """
        doc_nr_str = str(chr(64 + self.doc_nr)) if self.doc_nr else ''
        return '{} {:04d}{:02d}{:02d} {} {:02d}{}'.format(self.context,
                                                          self.datum.year,
                                                          self.datum.month,
                                                          self.datum.day,
                                                          self.punt_type.upper(),
                                                          self.punt_nr,
                                                          doc_nr_str)

class AgendaName(DocumentName):
    """docstring for DocumentVersion."""
    def __init__(self, context, datum):
        assert context in ('VR', 'VE', 'OC')
        super().__init__()
        self.context = context
        self.datum = datum

    def name(self):
        """ VR AGENDA 20021122 """
        return '{} AGENDA {}{:02d}{:02d}'.format(self.context.upper(),
                                                 self.datum.year,
                                                 self.datum.month,
                                                 self.datum.day)

class VrBeslissingsficheName(VersionedDocumentName):
    """docstring for DocumentVersion."""
    def __init__(self, context, year, zitting_nr, punt_nr=None, punt_type='PUNT'):
        assert context in ('VR', 'VE')
        assert punt_type in ('PUNT', 'MEDEDELING', 'VARIA')
        super().__init__()
        self.context = context
        self.year = year
        self.zitting_nr = zitting_nr
        self.punt_nr = punt_nr
        self.punt_type = punt_type

    def name(self):
        """ VR PV 2008/03 - PUNT 0016 """
        punt_nr_str =  ' {:04d}'.format(self.punt_nr) if self.punt_nr != None else ''
        return '{} PV {:04d}/{:02d} - {}{}'.format(self.context.upper(),
                                                   self.year,
                                                   self.zitting_nr,
                                                   self.punt_type,
                                                   punt_nr_str)

class OcBeslissingsficheName(DocumentName):
    """docstring for DocumentVersion."""
    def __init__(self, context, datum, punt_nr, punt_type='PUNT'):
        assert context in ('OC')
        assert punt_type in ('PUNT', 'MEDEDELING', 'VARIA')
        super().__init__()
        self.context = context
        self.datum = datum
        self.punt_nr = punt_nr
        self.punt_type = punt_type

    def name(self):
        """ OC 20181107 PUNT 05ATER """
        return '{} {:04d}{:02d}{:02d} {} {:02d}'.format(self.context.upper(),
                                                        self.datum.year,
                                                        self.datum.month,
                                                        self.datum.day,
                                                        self.punt_type,
                                                        self.punt_nr)

class VrNotulenName(VersionedDocumentName):
    def __init__(self, context, jaar, zitting_nr):
        assert context in ('VR', 'VE', 'OC')
        super().__init__()
        self.context = context
        self.jaar = jaar
        self.zitting_nr = zitting_nr

    def name(self):
        """ VR PV 2000/12 """
        return '{} PV {:04d}/{:02d}'.format(self.context.upper(),
                                            self.jaar,
                                            self.zitting_nr)
            