select  p.node_properties, n.node_properties
from edges e
join nodes p on p.node_id = e.node_id_from
join nodes n on n.node_id = e.node_id_to