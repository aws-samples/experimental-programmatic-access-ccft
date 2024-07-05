CREATE EXTERNAL TABLE IF NOT EXISTS `${database_name}`.`carbon_emissions_table` (
  `accountid` string, 
  `query` struct<queryDate:date,
                startDate:date,
                endDate:date>, 
  `emissions` struct<carbonEmissionEntries:array<struct<mbmCarbon:decimal(10,5),paceProductCode:string,regionCode:string,startDate:date>>,
                    carbonEmissionsForecast:array<struct<carbonInefficiency:decimal(10,5),mbmCarbon:decimal(10,5),startDate:date>>,
                    carbonEmissionsInefficiency:array<struct<gridMixInefficiency:decimal(10,5),serverHighInefficiency:decimal(10,5),
                                      serverLowInefficiency:decimal(10,5),serverMedianInefficiency:decimal(10,5),startDate:date>>> )
ROW FORMAT SERDE 
  'org.openx.data.jsonserde.JsonSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.IgnoreKeyTextOutputFormat'
LOCATION
  '${emissions_location}'