#!/usr/bin/python3
import uuid

from rdflib.namespace import RDF, XSD
from rdflib import URIRef, Literal

class MuFile:
    """docstring for MuFile."""
    def __init__(self):
        super().__init__()
        self.uuid = str(uuid.uuid1())
        self.physical_uuid = str(uuid.uuid1())
        self.name = None
        self.physical_name = None
        self.size = None
        self.mimetype = None
        self.extension = None
        self.created = None
        self.folder_path = ''

    @classmethod
    def from_document_version(cls, doc):
        file = cls()
        file.name = doc.name
        file.physical_name = doc.id
        file.extension = doc.extension()
        file.mimetype = doc.mimetype
        return file

    def uri(self, base_uri):
        return base_uri + "files/" + "{}".format(self.uuid)

    @property
    def physical_uri(self):
        return "share://{}{}.{}".format(self.folder_path, self.physical_name, self.extension)

    def materialize_metadata(self, metadata_lut):
        try:
            f = metadata_lut[self.physical_name + '.' + self.extension]
            if f['filesize']['succes']:
                self.size = f['filesize']['parsed']
            if f['creation_date']['succes']:
                self.created = f['creation_date']['parsed']
        except KeyError:
            pass

    def triples(self, ns, base_uri):
        virtual_file_uri = URIRef(self.uri(base_uri))
        physical_file_uri = URIRef(self.physical_uri)
        triples = [
            (virtual_file_uri, RDF['type'], ns.NFO['FileDataObject']),
            (virtual_file_uri, ns.MU['uuid'], Literal(self.uuid)),
            (virtual_file_uri, ns.NFO['fileName'], Literal(self.name)),
            (virtual_file_uri, ns.DCT['format'], Literal(self.mimetype)),
            (virtual_file_uri, ns.DBPEDIA['fileExtension'], Literal(self.extension)),

            (physical_file_uri, RDF['type'], ns.NFO['FileDataObject']),
            (physical_file_uri, ns.MU['uuid'], Literal(self.physical_uuid)),
            (physical_file_uri, ns.NFO['fileName'], Literal(self.physical_name)),
            (physical_file_uri, ns.DCT['format'], Literal(self.mimetype)),
            (physical_file_uri, ns.DBPEDIA['fileExtension'], Literal(self.extension)),
            (physical_file_uri, ns.NIE['dataSource'], virtual_file_uri),
        ]
        if self.size is not None:
            triples += [
                (virtual_file_uri, ns.NFO['fileSize'], Literal(self.size)),
                (physical_file_uri, ns.NFO['fileSize'], Literal(self.size)),
            ]
        if self.created:
            triples += [
                (virtual_file_uri, ns.DCT['created'], Literal(self.created.isoformat().replace('+00:00', 'Z'), datatype=XSD.dateTime)),
                (physical_file_uri, ns.DCT['created'], Literal(self.created.isoformat().replace('+00:00', 'Z'), datatype=XSD.dateTime)),
            ]
        return triples
