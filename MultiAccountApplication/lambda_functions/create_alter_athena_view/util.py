# Copyright 2024 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import time
from boto3 import client
import logging

log = logging.getLogger(__name__)
athena = client('athena')

class AthenaQueryExecutionException(Exception):
    pass

def load_query(filename, placeholders={}):

    with open(filename, 'r', encoding='utf-8') as file:
        statement = file.read()
    for name, replacement in placeholders.items():
        statement = statement.replace("${%s}" % name, replacement)
    return statement

def wait_for_query_execution(query_execution_id: str):
    while True:
        response = athena.get_query_execution(
            QueryExecutionId=query_execution_id
        )
        state = response['QueryExecution']['Status']['State']
        if state == 'SUCCEEDED':
            return
        elif state == 'FAILED' or state == 'CANCELLED':
            raise AthenaQueryExecutionException(f"Query {query_execution_id} failed: {response['QueryExecution']['Status']['StateChangeReason']}")
        time.sleep(2)

def run_query(query: str, workgroup_name: str):

    log.debug(f"Running query: \"{query}\" in workgroup: \"{workgroup_name}\"")

    params = {
        'QueryString': query,
        'WorkGroup': workgroup_name
    }

    response = athena.start_query_execution(**params)
    return wait_for_query_execution(response['QueryExecutionId'])
