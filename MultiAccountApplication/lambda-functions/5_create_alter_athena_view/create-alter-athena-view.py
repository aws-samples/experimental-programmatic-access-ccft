import boto3
import os

def lambda_handler(event, context):

    emissions_bucket = "s3://"+os.environ['emissionsBucketName']+"/"
    result_output_location = "s3://"+os.environ['athenaBucketName']+"/"

    # connect to the Athena client 
    athena_client = boto3.client('athena')

    # create a function that starts an Athena query execution
    def start_query_execution(query_string):
        athena_client.start_query_execution(QueryString=query_string, QueryExecutionContext={'Database': database_name,},ResultConfiguration={"OutputLocation": result_output_location})

    # create an Athena database
    database_name = os.environ['glueDatabaseName']
    create_database_query = f"CREATE DATABASE IF NOT EXISTS {database_name}"
    start_query_execution(create_database_query)

    # create an Athena table (if not exists)
    TABLE_DDL = "create_table.ddl"
    with open(TABLE_DDL, 'r') as ddl:
        create_table_template = ddl.read()
        create_table_query = create_table_template.replace('location', emissions_bucket)
    start_query_execution(create_table_query)
    
    # create or replace Athena view
    with open("create_view.sql", 'r') as sql:
        create_view_query = sql.read()
    start_query_execution(create_view_query)

    return {
        'statusCode': 200,
    }