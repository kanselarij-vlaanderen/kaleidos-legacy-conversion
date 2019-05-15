SELECT 
taxonomy_term_data.tid as id,
taxonomy_term_data.name as name,
taxonomy_term_data.description as description

FROM
`taxonomy_term_data`
WHERE
`vid` = '2'
ORDER BY
`tid`;
