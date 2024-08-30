import os
import util

def lambda_handler(*_):

    workgroup_name = os.environ['workgroupName']
    database_name = os.environ['glueDatabaseName']

    placeholders = {
        "emissions_location": "s3://"+os.environ['emissionsBucketName']+"/",
        "database_name": database_name
    }

    util.run_query(f"CREATE DATABASE IF NOT EXISTS {database_name}", workgroup_name)

    util.run_query(util.load_query('create_table.ddl', placeholders), workgroup_name)
    
    util.run_query(util.load_query('create_view.sql', placeholders), workgroup_name)

    util.run_query(util.load_query('create_aggregate_view.sql', placeholders), workgroup_name)

    util.run_query(util.load_query('create_forecast_view.sql', placeholders), workgroup_name)

    return None
