#!/usr/bin/python3
import logging
from .model.oc_document import Document

def create_documents(document_versions):
    documents_by_name = {}

    for document_version in document_versions:
        if document_version.parsed_name:
            name = document_version.parsed_name.name()
        else:
            name = document_version.source_name
        if document_version.version:
            version = document_version.version
        else:
            version = 1
        try:
            document = documents_by_name[name]
            if any(version == ver for ver, doc in document.document_versions):
                logging.warning("Already a version '{}' in the versions collection of document '{}'".format(version, name))
            document.document_versions.append((version, document_version))
        except KeyError:
            document = Document(document_version)
            documents_by_name[name] = document
        document_version.document = document
    return documents_by_name.values()
