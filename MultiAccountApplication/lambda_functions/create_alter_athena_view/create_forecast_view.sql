CREATE OR REPLACE VIEW "${database_name}"."carbon_emissions_forecast_view" AS
SELECT
  cet.accountid
, forecast.carboninefficiency
, forecast.mbmCarbon
, forecast.startDate as years
FROM
  ("${database_name}"."carbon_emissions_table" cet
CROSS JOIN UNNEST(cet.emissions.carbonEmissionsForecast) AS t(forecast))
