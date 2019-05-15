#!/usr/bin/python3

from .model.document import Document

def create_documents(document_versions):
    return list([Document(doc_ver) for doc_ver in document_versions])
