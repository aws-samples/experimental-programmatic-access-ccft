CREATE OR REPLACE VIEW "${database_name}"."carbon_emissions_aggregate_view" AS 
SELECT
  cet.accountid
, cet.query.querydate
, entries.startdate
, SUM(entries.mbmcarbon) mbmcarbon
, inefficiency.gridmixinefficiency gridmixinefficiency
, inefficiency.servermedianinefficiency servermedianinefficiency
FROM
  (("${database_name}"."carbon_emissions_table" cet
CROSS JOIN UNNEST(cet.emissions.carbonemissionentries) t (entries))
CROSS JOIN UNNEST(cet.emissions.carbonemissionsinefficiency) t (inefficiency))
WHERE (entries.startdate = inefficiency.startdate)
GROUP BY cet.accountid, cet.query.querydate, entries.startdate, inefficiency.gridmixinefficiency, inefficiency.servermedianinefficiency
