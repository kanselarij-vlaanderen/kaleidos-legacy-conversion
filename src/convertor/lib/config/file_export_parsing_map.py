#!/usr/bin/python3

import lib.doris_export_parsers as parsers


custom_trans_file = {
    'r_object_id': {'parser': parsers.p_object_id, 'required': True},
    'object_name': {'parser': str, 'required': True},
    'a_content_type': {'parser': parsers.p_content_type, 'required': True},
}
