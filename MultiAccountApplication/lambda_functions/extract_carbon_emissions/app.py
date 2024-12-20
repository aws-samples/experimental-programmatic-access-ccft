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

import json
import logging
import os
from urllib.parse import urlencode

import boto3
import ccft_access

s3 = boto3.resource("s3")
sts_client = boto3.client("sts")
s3_bucket = os.environ["bucketName"]
role_name = os.environ["ccftRole"]
s3_obj_name = os.environ["fileName"]

log = logging.getLogger(__name__)


def lambda_handler(event, context):
    """Lambda handler to retrieve and write ccft data to S3 for the timeframe from start_date to
    end_date.

    Args:
        event: the AWS Lambda event.

            Must contain:

            - AWS account id as event/account
            - query start date as event/timeframe/start_date
            - query end date as event/timeframe/end_date

            May contain:

            - skip_write: if set to True, the function will not write the data to S3

        context: the AWS Lambda context

    Raises:
        ValueError: if the event does not contain start_date and end_date

    Returns:
        isDataAvailable: if data is available for the given timeframe
    """
    # get start/ end/ account from the event
    # validate argument event[timeframe]['start'] and event[timeframe]['end']
    if (
        "timeframe" not in event
        or "end_date" not in event["timeframe"]
        or "start_date" not in event["timeframe"]
    ):
        raise ValueError(
            "event must have dates (YYYY-MM-DD) in event/timeframe/start_date and event/timeframe/end_date"
        )
    if "account" not in event:
        raise ValueError("event must have account-id in event/account")

    skip_write = ("skip_write" in event) and event["skip_write"]

    account = event["account"]
    start_date = event["timeframe"]["start_date"]
    end_date = event["timeframe"]["end_date"]

    request_id = context.aws_request_id

    # Create a new session and get credentials from target role
    target_account_role_arn = f"arn:aws:iam::{account}:role/{role_name}"
    target_account_role = sts_client.assume_role(
        RoleArn=target_account_role_arn, RoleSessionName="sustainability_reader_session"
    )

    new_access_key_id = target_account_role["Credentials"]["AccessKeyId"]
    new_secret_access_key = target_account_role["Credentials"]["SecretAccessKey"]
    new_session_token = target_account_role["Credentials"]["SessionToken"]

    new_session = boto3.Session(
        aws_access_key_id=new_access_key_id,
        aws_secret_access_key=new_secret_access_key,
        aws_session_token=new_session_token,
    )

    credentials = new_session.get_credentials()

    try:
        log.debug(f"Extracting emissions data from {start_date} to {end_date}")
        emissions_data = ccft_access.extract_emissions_data(
            start_date, end_date, credentials
        )

        # check if new emissions data is available
        carbonEmissionEntries = emissions_data["emissions"]["carbonEmissionEntries"]
        if not carbonEmissionEntries:
            isDataAvailable = False
            message = "No new data is available"
        else:
            isDataAvailable = True
            # save json to file in s3 bucket
            if skip_write:
                message = f"Skipped saving data for account {account}"
            else:
                s3_obj_name = (
                    f"{account}/{request_id}_{start_date}carbon_emissions.json"
                )
                s3.Object(s3_bucket, s3_obj_name).put(Body=json.dumps(emissions_data))
                message = f"Successfully saved data to S3 bucket for account {account}"
        return {"message": message, "isDataAvailable": isDataAvailable}

    except Exception as e:
        # If account is less than three months old, no carbon emissions data will be available
        message = str(e)

        if "404 Client Error: Not Found for url" in str(e):
            message = f"""No carbon footprint report is available for account {account} at this time.
If no report is available, your account might be too new to show data.
There is a delay of three months between the end of a month and when emissions data is available."""

        return {"message": message, "isDataAvailable": False}
