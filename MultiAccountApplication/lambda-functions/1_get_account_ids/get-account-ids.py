import boto3

def lambda_handler(event, context):
        
    # Create the AWS Organizations client
    org_client = boto3.client("organizations")
    
    # Get the paginator for the list_accounts operation
    paginator = org_client.get_paginator("list_accounts")
    
    # Retrieve all account IDs in the organization
    accounts = [account["Id"] for page in paginator.paginate() for account in page["Accounts"]]

    # Retrieve the ID of the management account
    management_account_id = org_client.describe_organization()['Organization']['MasterAccountId']

    return {
        'statusCode': 200,
        'account_ids': accounts,
        'account_id': management_account_id
    }