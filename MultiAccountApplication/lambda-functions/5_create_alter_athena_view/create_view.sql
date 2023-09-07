CREATE OR REPLACE VIEW "carbon_emissions_view" AS
SELECT 
    cet.accountid,
    cet.query.querydate,
    entries.startdate,
    entries.mbmcarbon,
    entries.paceproductcode,
    entries.regioncode,
    inefficiency.gridmixinefficiency,
    inefficiency.servermedianinefficiency
FROM "carbon_emissions_table" cet
CROSS JOIN UNNEST(cet.emissions.carbonemissionentries) t (entries)
CROSS JOIN UNNEST(cet.emissions.carbonemissionsinefficiency) t (inefficiency)
WHERE entries.startdate = inefficiency.startdate;
