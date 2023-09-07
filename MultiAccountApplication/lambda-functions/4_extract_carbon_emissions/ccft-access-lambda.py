# Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# This resembles the access to AWS Customer Carbon Footprint Tool data
# from the AWS Billing Console. Hence it is not using an official AWS interface and
# might change at any time without notice and just stop working.

import boto3
import os
import ccft_access
import json
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from urllib.parse import urlencode


def lambda_handler(event, context):
    account = event
    s3 = boto3.resource('s3')
    sts_client = boto3.client('sts')
    s3_bucket = os.environ['bucketName']
    role_name = os.environ['ccftRole']
    s3_obj_name = os.environ['fileName']
    request_id = context.aws_request_id

    # calculate three months past (when new carbon emissions data is available)
    three_months = date.today() + relativedelta(months=-3)
    # get the date with 1st day of the month
    year = three_months.year
    month = three_months.month
    first_date = datetime(year, month, 1)
    
    # If you want to extract carbon emissions data for a different time frame, you can change it manually here
    start_date=first_date.strftime("%Y-%m-%d")
    end_date=first_date.strftime("%Y-%m-%d")

    # Create a new session and get credentials from target role
    target_account_role_arn = f"arn:aws:iam::{account}:role/{role_name}"
    target_account_role = sts_client.assume_role(
        RoleArn=target_account_role_arn,
        RoleSessionName="sustainability_reader_session"
    )
    
    new_access_key_id = target_account_role["Credentials"]["AccessKeyId"]
    new_secret_access_key = target_account_role["Credentials"]["SecretAccessKey"]
    new_session_token = target_account_role["Credentials"]["SessionToken"]

    new_session = boto3.Session(
        aws_access_key_id=new_access_key_id,
        aws_secret_access_key=new_secret_access_key,
        aws_session_token=new_session_token
    )
    
    credentials = new_session.get_credentials()

    try:
        emissions_data = ccft_access.extract_emissions_data(start_date, end_date, credentials)

        # check if new emissions data is available
        carbonEmissionEntries = emissions_data['emissions']['carbonEmissionEntries']
        if len(carbonEmissionEntries) == 0:
            isDataAvailable = False
            message = "No new data is available"
        else:
            isDataAvailable = True
            # save json to file in s3 bucket
            s3_obj_name = str(account)+"/"+str(request_id)+"_"+str(start_date)+"carbon_emissions.json"
            s3.Object(s3_bucket, s3_obj_name).put(Body=json.dumps(emissions_data))
            message = "Successfully saved data to S3 bucket for account", account
        
        return {
            'message': message,
            'isDataAvailable': isDataAvailable
        }        

    except Exception as e:
        #If account is less than three months old, no carbon emissions data will be available
        message = str(e)
        if str(e) == "404 Client Error: Not Found for url: https://us-east-1.console.aws.amazon.com/billing/rest/api-proxy/carbonfootprint":
            message = "No carbon footprint report is available for account", account, "at this time. If no report is available, your account might be too new to show data. There is a delay of three months between the end of a month and when emissions data is available."
        return {
                'message': message,
                'isDataAvailable': False
            }
