SELECT
node.nid as nid,
node.title as title,
field_data_field_first_name.field_first_name_value AS first_name, 
field_data_field_surname.field_surname_value AS surname, 
field_data_field_start_date.field_start_date_value AS start_date, 
field_data_field_end_date.field_end_date_value AS end_date, 
field_data_field_order.field_order_value AS 'order', 
field_data_field_official_title.field_official_title_value AS official_title, 
field_data_field_editorial_title.field_editorial_title_value AS editorial_title_key, 
field_data_field_e_mailaddress.field_e_mailaddress_email AS e_mailaddress

FROM 
node

INNER JOIN field_data_field_first_name
ON nid = field_data_field_first_name.entity_id
INNER JOIN field_data_field_surname
ON nid = field_data_field_surname.entity_id
INNER JOIN field_data_field_start_date
ON nid = field_data_field_start_date.entity_id
INNER JOIN field_data_field_end_date
ON nid = field_data_field_end_date.entity_id
INNER JOIN field_data_field_order
ON nid = field_data_field_order.entity_id
INNER JOIN field_data_field_official_title
ON nid = field_data_field_official_title.entity_id
INNER JOIN field_data_field_editorial_title
ON nid = field_data_field_editorial_title.entity_id
INNER JOIN field_data_field_e_mailaddress
ON nid = field_data_field_e_mailaddress.entity_id

WHERE
node.type = 'toeleveringskanaal'

ORDER BY
start_date
