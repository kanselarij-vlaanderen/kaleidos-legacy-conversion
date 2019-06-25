SELECT
node.nid as nid,
node.vid as vid,
STR_TO_DATE(SUBSTRING(node.title, 1, 6), '%d%m%y') AS agenda_date,
field_data_field_date.field_date_value AS date_published,
field_data_field_meeting_sequence.field_meeting_sequence_value AS meeting_sequence,
field_data_field_documents_date_published.field_documents_date_published_value AS documents_date_published,
node.status as status,
field_data_field_agendanumber.field_agendanumber_value AS agenda_item_nr, 
field_data_field_description.field_description_value AS description, 
field_data_body.body_value AS body_value, 
field_data_body.body_format AS body_format, 
GROUP_CONCAT(field_data_field_policy_area.field_policy_area_target_id) AS policy_area_ids,
GROUP_CONCAT(field_data_field_minister.field_minister_target_id) AS minister_ids,
GROUP_CONCAT(field_data_field_doris_object_id.field_doris_object_id_value) AS document_ids

FROM 
node

LEFT JOIN field_data_field_agendanumber
ON nid = field_data_field_agendanumber.entity_id AND vid = field_data_field_agendanumber.revision_id
LEFT JOIN field_data_field_description
ON nid = field_data_field_description.entity_id AND vid = field_data_field_description.revision_id
LEFT JOIN field_data_body
ON nid = field_data_body.entity_id AND vid = field_data_body.revision_id
LEFT JOIN field_data_field_policy_area
ON nid = field_data_field_policy_area.entity_id AND vid = field_data_field_policy_area.revision_id
LEFT JOIN field_data_field_minister
ON nid = field_data_field_minister.entity_id AND vid = field_data_field_minister.revision_id
LEFT JOIN field_data_field_kortbestek
ON nid = field_data_field_kortbestek.entity_id AND vid = field_data_field_kortbestek.revision_id
LEFT JOIN field_data_field_date
ON field_data_field_kortbestek.field_kortbestek_target_id = field_data_field_date.entity_id
LEFT JOIN field_data_field_meeting_sequence
ON field_data_field_kortbestek.field_kortbestek_target_id = field_data_field_meeting_sequence.entity_id
LEFT JOIN field_data_field_documents_date_published
ON field_data_field_kortbestek.field_kortbestek_target_id = field_data_field_documents_date_published.entity_id
LEFT JOIN field_data_field_documents
ON nid = field_data_field_documents.entity_id AND vid = field_data_field_documents.revision_id
LEFT JOIN field_data_field_doris_object_id
ON field_data_field_documents.field_documents_target_id = field_data_field_doris_object_id.entity_id

WHERE
node.type = 'agendapunt'

GROUP BY
node.nid,
field_data_field_agendanumber.field_agendanumber_value,
field_data_field_date.field_date_value,
field_data_field_meeting_sequence.field_meeting_sequence_value,
field_data_field_documents_date_published.field_documents_date_published_value,
field_data_field_description.field_description_value,
field_data_body.body_value,
field_data_body.body_format;
