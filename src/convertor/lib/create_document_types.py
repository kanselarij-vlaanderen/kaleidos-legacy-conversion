#!/usr/bin/python3

from .code_lists.document_types import DOCUMENT_TYPES
from .model.document_type import DocumentType

def create_document_types():
    """
    Returns dict of DocumentTypes by label
    """

    document_types = {}
    for document_type in DOCUMENT_TYPES:
        document_types[document_type[0]] = DocumentType(*document_type)
    return document_types
