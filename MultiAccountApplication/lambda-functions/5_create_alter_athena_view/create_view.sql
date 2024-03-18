CREATE OR REPLACE VIEW "carbon_emissions_view" AS 
SELECT
  cet.accountid
, cet.query.querydate
, entries.startdate
, entries.mbmcarbon
, entries.paceproductcode
, entries.regioncode
FROM
  ("carbon_emissions_table" cet
CROSS JOIN UNNEST(cet.emissions.carbonemissionentries) t (entries))
