import boto3
import os

def lambda_handler(event, context):

    # Create the AWS Organizations client
    org_client = boto3.client('organizations')
    # Retrieve all account IDs in the organization
    accounts = org_client.list_accounts()
    account_ids = [account['Id'] for account in accounts['Accounts']]

    # Retrieve the ID of the management account
    management_account_id = org_client.describe_organization()['Organization']['MasterAccountId']

    return {
        'statusCode': 200,
        'account_ids': account_ids,
        'account_id': management_account_id
    }
