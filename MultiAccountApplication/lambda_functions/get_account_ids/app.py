import boto3
from datetime import datetime, date
import logging
from dateutil.relativedelta import relativedelta

log = logging.getLogger(__name__)

def create_timeframes(today:str):
    """Calculate the timeframes for the backfill and the checking/ loading of new data.

    Args:
        today (str): today in the format of YYYY-MM-DD
    """
    today_date = datetime.strptime(today, '%Y-%m-%d').date()
    
    # 1. new data: calculate three months past (when new carbon emissions data
    # is available)
    three_months = today_date - relativedelta(months=3)
    # get the date with 1st day of the month
    # the start data will be used for both as start and end of a query
    start_new_data = three_months.replace(day=1).strftime("%Y-%m-%d")

    # 2. backfill: since the maximum time to extract carbon emissions data is 36
    # months, we can use the timeframe from 40-4 months back
    four_months = today_date - relativedelta(months=4)
    forty_months = today_date - relativedelta(months=40)

    start_backfill = forty_months.replace(day=1).strftime("%Y-%m-%d")
    end_backfill = four_months.replace(day=1).strftime("%Y-%m-%d")

    return { 'timeframes': {
        'backfill': {
            'start_date': start_backfill,
            'end_date': end_backfill
        },
        'new_data': {
            'start_date': start_new_data,
            'end_date': start_new_data
        }
    }}

def lambda_handler(event, _):

    today = date.today().strftime("%Y-%m-%d")
    
    if ('override_today' in event):
        today = event['override_today']

    log.debug(f"Pulling data relative to {today}")

    timeframes = create_timeframes(today)

    accounts = []

    if ('override_accounts' in event):
        accounts = event['override_accounts']
    else:
        # Create the AWS Organizations client
        org_client = boto3.client("organizations")
        
        # Get the paginator for the list_accounts operation
        paginator = org_client.get_paginator("list_accounts")
        
        # Retrieve the ID of the management account
        management_account_id = org_client.describe_organization()['Organization']['MasterAccountId']

        # Retrieve all account IDs in the organization
        accounts = [account["Id"] for page in paginator.paginate() for account in page["Accounts"]]

        # move the management account to the first index
        accounts.remove(management_account_id)
        accounts = [management_account_id] + accounts

    return {
        'account_ids': accounts
    } | timeframes
