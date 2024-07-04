CREATE OR REPLACE VIEW "${database_name}"."carbon_emissions_view" AS 
SELECT
  cet.accountid
, cet.query.querydate
, entries.startdate
, entries.mbmcarbon
, entries.paceproductcode
, entries.regioncode
FROM
  ("${database_name}"."carbon_emissions_table" cet
CROSS JOIN UNNEST(cet.emissions.carbonemissionentries) t (entries))
