# Copyright 2025 Amazon.com, Inc. or its affiliates. All Rights Reserved.
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

import argparse
import json
import sys
from datetime import datetime, timezone

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from dateutil.relativedelta import relativedelta


def extract_emissions_data(startDate, endDate, credentials):
    billing_region = "us-east-1"
    host = f"{billing_region}.prod.sustainability.billingconsole.aws.dev"
    url = f"https://{host}/get-carbon-footprint-summary?startDate={startDate}&endDate={endDate}"
    method = "GET"

    if credentials.token is None:
        # this is most likely an IAM or root user
        exit("You seem to run this with an IAM user. Assume an account's role instead.")

    # get the account ID to include it in the response
    sts_client = boto3.client(
        "sts",
        aws_access_key_id=credentials.access_key,
        aws_secret_access_key=credentials.secret_key,
        aws_session_token=credentials.token,
    )

    accountID = sts_client.get_caller_identity()["Account"]

    request = AWSRequest(method, url, headers={"Host": host})

    SigV4Auth(credentials, "sustainability", billing_region).add_auth(request)

    try:
        response = requests.request(
            method, url, headers=dict(request.headers), data={}, timeout=5
        )
        response.raise_for_status()
    except Exception as e:
        if "404 Client Error: Not Found for url" in str(e):
            raise Exception(
                f"""No carbon footprint report is available for account {accountID} at this time.
If no report is available, your account might be too new to show data.
There is a delay of three months between the end of a month and when emissions data is available."""
            )
        else:
            raise Exception("An error occured: " + str(e))

    emissions = response.json()

    emissions_data = {
        "accountId": accountID,
        "query": {
            "queryDate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "startDate": startDate,
            "endDate": endDate,
        },
        "emissions": emissions,
    }

    print(json.dumps(emissions_data))
    return emissions_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Script to extract carbon emissions from the AWS Customer Carbon Footprint Tool."
    )

    # calculate three months past (when new carbon emissions data is available)
    three_months = datetime.now(timezone.utc) - relativedelta(months=3)
    # get the date with 1st day of the month
    year = three_months.year
    month = three_months.month
    first_date = datetime(year, month, 1)

    # The default end date is the first date of the month three months ago, and the default start date is 36 months before
    default_end_date = first_date.strftime("%Y-%m-%d")
    default_start_date = (first_date - relativedelta(months=36)).strftime("%Y-%m-%d")

    parser = argparse.ArgumentParser(
        description="""Experimental retrieval of AWS Customer Carbon Footprint Tool console data.
        The data is queried for a closed interval from START_DATE to END_DATE (YYYY-MM-DD).
        The queried timeframe must be less than 36 months and not before 2020-01-01."""
    )
    parser.add_argument(
        "--start-date",
        "-s",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
        default=datetime.strptime(default_start_date, "%Y-%m-%d"),
        help=f"first month of the closed interval, default 36 months before end date: {default_start_date}",
    )
    parser.add_argument(
        "--end-date",
        "-e",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
        default=datetime.strptime(default_end_date, "%Y-%m-%d"),
        help=f"last month of the closed interval, default 3 months before current date: {default_end_date}",
    )

    args = parser.parse_args()
    start_date = args.start_date.strftime("%Y-%m-%d")
    end_date = args.end_date.strftime("%Y-%m-%d")

    session = boto3.Session()
    credentials = session.get_credentials()

    if credentials is None:
        exit(
            'You need to configure an AWS profile with an IAM role to run this script (see FAQ "How do I use the script?").'
        )

    try:
        extract_emissions_data(start_date, end_date, credentials)

    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(1)
