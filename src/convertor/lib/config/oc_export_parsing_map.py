#!/usr/bin/python3

import lib.doris_export_parsers as parsers


# "r_object_id"; "object_name"; "title"; "a_content_type"; "DAR_UPDATE";
# "dar_indiener_samenvatting"; "dar_vervangt"; "dar_restricted"; "dar_err_date";
# "dar_te_stempelen"; "DAR_DOC_TYPE"; "dar_verg_nr"; "DAR_AANVULLEND"; "dar_volgnummer";
# "dar_indiener"; "dar_levenscyclus_status"; "dar_besl_vereist"; "dar_onderwerp";
# "dar_titel_indiener"; "dar_vorige"; "dar_document_nr"; "dar_date_vergadering";
# "dar_verg_type"; "dar_restricted_tmp"; "dar_context"; "dar_pub_date";"DAR_TER_VERGADERING";
# "dar_notif_nr"; "dar_zoek_datum_vergadering"; "dar_datum_vergadering"; "dar_aard";
# "dar_keywords"; "gerelateerde documenten";

custom_trans_document = {
    'r_object_id': {'parser': parsers.p_object_id, 'required': True},
    'object_name': {'parser': parsers.p_oc_doc_name, 'required': False},
    'a_content_type': {'parser': parsers.p_content_type, 'required': True},
    # 'dar_update': {'parser': parsers.p_true_false, 'required': False}, # Wordt niet gebruikt
    'dar_indiener_samenvatting': {'parser': parsers.p_administration_indiener, 'required': False},
    # 'dar_vervangt': {'parser': parsers.p_doc_name, 'required': False}, # Werd vroeger gebruikt, 'required': False}, nu niet meer
    'dar_restricted': {'parser': parsers.p_true_false, 'required': False},
    # 'dar_err_date': {'parser': parsers.p_keyed_dates, 'required': False},
    'dar_doc_type': {'parser': parsers.p_doc_type, 'required': False},
    'dar_verg_nr': {'parser': parsers.p_oc_session_number, 'required': True},
    # 'dar_aanvullend': {'parser': parsers.p_doc_name, 'required': False}, # Werd vroeger gebruikt, 'required': False}, nu niet meer
    'dar_volgnummer': {'parser': parsers.p_number, 'required': False},
    'dar_levenscyclus_status': {'parser': parsers.p_lifecycle_state, 'required': False},
    # 'dar_besl_vereist': {'parser': parsers.p_true_false, 'required': False}, # Wordt niet gebruikt
    # 'dar_onderwerp': {'parser': , 'required': False},
    # 'dar_vorige': {'parser': parsers.p_doc_list, 'required': False}, # List gets parsed later on
    'dar_date_vergadering': {'parser': parsers.p_datetime, 'required': False},
    # 'dar_verg_type':, 'required': False}, # Wordt niet gebruikt
    'dar_restricted_tmp': {'parser': parsers.p_true_false, 'required': False}, # Always False?
    # 'dar_pub_date': {'parser': parsers.p_keyed_dates, 'required': False},
    # 'dar_ter_vergadering': {'parser': parsers.p_true_false, 'required': False}, # Only 50 or so true ... not to be trusted field?
    # 'dar_zoek_datum_vergadering': {'parser': parsers.p_datetime, 'required': False}, # Always same as dar_date_vergadering?
    'dar_datum_vergadering': {'parser': parsers.p_datetime, 'required': False}, # Always nulldate?
    # 'dar_aard': {'parser': parsers.p_aard, 'required': False}, # Wordt niet gebruikt
    'dar_keywords': {'parser': parsers.p_keywords, 'required': False},
}

# "r_object_id"; "object_name"; "title"; "a_content_type"; "dar_indiener_samenvatting";
# "dar_vervangt"; "dar_restricted"; "dar_err_date"; "DAR_REL_DOCS"; "dar_verg_nr";
# "dar_volgnummer"; "dar_indiener"; "dar_levenscyclus_status"; "dar_besl_vereist";
# "dar_onderwerp"; "dar_titel_indiener"; "dar_vorige"; "dar_document_nr";"dar_date_vergadering";
# "dar_verg_type"; "dar_restricted_tmp"; "dar_context"; "dar_pub_date"; "dar_notif_nr";
# "dar_zoek_datum_vergadering"; "DAR_FICHE_TYPE"; "dar_datum_vergadering"; "dar_aard";
# "dar_keywords"; "DAR_OLDDOC_TYPE"; "gerelateerde documenten";

custom_trans_fiche = {
    'r_object_id': {'parser': parsers.p_object_id, 'required': True},
    'object_name': {'parser': parsers.p_oc_agendapunt_name, 'required': False},
    'a_content_type': {'parser': parsers.p_content_type, 'required': True},
    # 'dar_indiener_samenvatting': {'parser': parsers.p_indiener_samenvatting, 'required': False},
    'dar_restricted': {'parser': parsers.p_true_false, 'required': False},
    'dar_err_date': {'parser': parsers.p_keyed_dates, 'required': False},
    'dar_rel_docs': {'parser': lambda r: parsers.p_doc_list(r.upper()), 'required': False}, # List gets parsed later on
    'dar_verg_nr': {'parser': parsers.p_oc_session_number, 'required': True},
    'dar_volgnummer': {'parser': parsers.p_number, 'required': False},
    'dar_levenscyclus_status': {'parser': parsers.p_lifecycle_state, 'required': False},
    # 'dar_besl_vereist': {'parser': parsers.p_true_false, 'required': False}, # Wordt niet gebruikt
    # 'dar_onderwerp': {'parser': , 'required': False},
    # 'dar_vorige': {'parser': parsers.p_doc_list, 'required': False}, # List gets parsed later on
    'dar_date_vergadering': {'parser': parsers.p_datetime, 'required': False},
    # 'dar_verg_type': {'parser': parsers.p_verg_type, 'required': False}, # Werd vroeger gebruikt, 'required': False}, nu niet meer
    'dar_restricted_tmp': {'parser': parsers.p_true_false, 'required': False},
    'dar_pub_date': {'parser': parsers.p_keyed_dates, 'required': False},
    'dar_zoek_datum_vergadering': {'parser': parsers.p_datetime, 'required': False},
    'dar_fiche_type': {'parser': parsers.p_doc_type, 'required': False},
    'dar_datum_vergadering': {'parser': parsers.p_datetime, 'required': False},
    # 'dar_aard': {'parser': parsers.p_aard, 'required': False}, # QUESTION: Welke codelijst precies?
    'dar_keywords': {'parser': parsers.p_keywords, 'required': False},
    # 'dar_olddoc_type': {'parser': parsers.p_true_false, 'required': False},
    # 'dar_needs_update': {'parser': parsers.p_true_false, 'required': False},
}
