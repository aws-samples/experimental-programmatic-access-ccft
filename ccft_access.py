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
import requests
import argparse
import json
from urllib.parse import urlencode
from datetime import datetime
import sys
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

def extract_emissions_data(startDate, endDate, credentials):
    billing_region = 'us-east-1'

    if credentials.token is None:
        # this is most likely an IAM or root user
        exit("You seem to run this with an IAM user. Assume an account's role instead.")

    #get the account ID to include it in the response
    sts_client = boto3.client(
         'sts',
         aws_access_key_id=credentials.access_key,
         aws_secret_access_key=credentials.secret_key,
         aws_session_token=credentials.token
    )

    accountID = sts_client.get_caller_identity()["Account"]

    # Create a new session in which all cookies are set during login
    s = requests.Session()

    aws_federated_signin_endpoint = 'https://signin.aws.amazon.com/federation'

    # Get SigninToken
    signin_token_params = {
        "Action": "getSigninToken",
        "Session": {
            "sessionId": credentials.access_key,
            "sessionKey": credentials.secret_key,
            "sessionToken": credentials.token
        }
    }
    signin_token_url = "%s?%s" % (
        aws_federated_signin_endpoint, urlencode(signin_token_params))
    signin_token_request = s.get(signin_token_url)
    signin_token = json.loads(signin_token_request.text)['SigninToken']

    # Create Login URL
    login_params = {
        "Action": "login",
        "Destination": "https://console.aws.amazon.com/",
        "SigninToken": signin_token
    }
    login_url = "%s?%s" % (aws_federated_signin_endpoint, urlencode(login_params))

    r = s.get(login_url)
    r.raise_for_status()

    # grap the xsrf token once
    r = s.get("https://console.aws.amazon.com/billing/home?state=hashArgs")
    r.raise_for_status()
    xsrf_token = r.headers["x-awsbc-xsrf-token"]

    # call the proxy via POST
    cft_request = {
        "headers": {
            "Content-Type": "application/json"
        },
        "path": "/get-carbon-footprint-summary",
        "method": "GET",
        "region": billing_region,
        "params": {
            "startDate": startDate,
            "endDate": endDate
        }
    }
    cft_headers = {
        "x-awsbc-xsrf-token": xsrf_token
    }

    try:
        r = s.post(
            "https://%s.console.aws.amazon.com/billing/rest/api-proxy/carbonfootprint" % (billing_region),
            data=json.dumps(cft_request),
            headers=cft_headers
        )
        r.raise_for_status()
        emissions = r.json()

        emissions_data = {
            "accountId": accountID,
            "query": {
                "queryDate": datetime.today().strftime("%Y-%m-%d"),
                "startDate": startDate,
                "endDate": endDate,
            },
            "emissions": emissions
        }

        print(json.dumps(emissions_data))
        return emissions_data

    except Exception as e:
            if str(e) == "404 Client Error: Not Found for url: https://us-east-1.console.aws.amazon.com/billing/rest/api-proxy/carbonfootprint":
                raise Exception("No carbon footprint report is available for this account at this time. If no report is available, your account might be too new to show data. There is a delay of three months between the end of a month and when emissions data is available.")
            else:
                raise Exception("An error occured: " + str(e))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=
    "Script to extract carbon emissions from the AWS Customer Carbon Footprint Tool.")

    # calculate three months past (when new carbon emissions data is available)
    three_months = date.today() - relativedelta(months=3)
    # get the date with 1st day of the month
    year = three_months.year
    month = three_months.month
    first_date = datetime(year, month, 1)
    
    # The default end date is the first date of the month three months ago, and the default start date is 36 months before
    default_end_date=first_date.strftime("%Y-%m-%d")
    default_start_date=(first_date - relativedelta(months=36)).strftime("%Y-%m-%d")

    parser = argparse.ArgumentParser(description=
        """Experimental retrieval of AWS Customer Carbon Footprint Tool console data.
        The data is queried for a closed interval from START_DATE to END_DATE (YYYY-MM-DD).
        The queried timeframe must be less than 36 months and not before 2020-01-01.""")
    parser.add_argument('--start-date', '-s',
        type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
        default=datetime.strptime(default_start_date, "%Y-%m-%d"),
        help="first month of the closed interval, default 36 months before end date: %s" % default_start_date)
    parser.add_argument('--end-date', '-e',
        type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
        default=datetime.strptime(default_end_date, "%Y-%m-%d"),
        help="last month of the closed interval, default 3 months before current date: %s" % default_end_date)

    args = parser.parse_args()
    start_date=args.start_date.strftime("%Y-%m-%d")
    end_date=args.end_date.strftime("%Y-%m-%d")

    session = boto3.Session()
    credentials = session.get_credentials()

    try:
         extract_emissions_data(start_date, end_date, credentials)

    except Exception as e:
         sys.stderr.write(str(e))
         sys.exit(1)

