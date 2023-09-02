create materialized view task_table as
select /*+ Hash Join */ m.taxonname, a.composition, m.change_in_abundance, a.frequency, a.additive_type
from people p
join microorganisms m on p.id_subgroup = m.id_subgroup /*and p.id_group = m..id_group*/
join additives a on p.id_additive = a.id_additive /*or p.doi = a.doi*/;