# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import json
import boto3
import ccft_access
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

def lambda_handler(event, context):
    # calculate three months past (when new carbon emissions data is available)
    three_months = date.today() - relativedelta(months=3)
    # get the date with 1st day of the month
    year = three_months.year
    month = three_months.month
    first_date = datetime(year, month, 1)
    
    # The default end date is the first date of the month three months ago, and the default start date is 36 months before
    # If you want to extract carbon emissions data for a different time frame, you can change it manually here
    end_date=first_date.strftime("%Y-%m-%d")
    start_date=(first_date - relativedelta(months=36)).strftime("%Y-%m-%d")
    
    # get the account id to include it in the function invocation
    # if you want to extract carbon emissions data for a different account, you can change it here
    session = boto3.Session()
    credentials = session.get_credentials()
    
    try:
        emissions_data = ccft_access.extract_emissions_data(start_date, end_date, credentials)

        # optionally: you can directly store this into S3
        # s3 = boto3.resource('s3') 
        # s3.Object("<YOUR_S3_BUCKET_NAME>", "emissions.json").put(Body=json.dumps(emissions_data))

        return {
            'statusCode': 200,
            'body': emissions_data
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': str(e)
        }


