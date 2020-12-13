# Copyright 2020 Julien Mineraud <julien.mineraud@gmail.com>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import requests
import json
import logging
import boto3
from itertools import starmap

SUCCESS = "SUCCESS"
FAILED = "FAILED"
S3 = boto3.client('s3')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Based on https://github.com/ryansb/cfn-wrapper-python/blob/master/cfn_resource.py
def cfnresponse(event, context, responseStatus, physicalResourceId=None):

    response = {
        "StackId":
        event["StackId"],
        "RequestId":
        event["RequestId"],
        "LogicalResourceId":
        event["LogicalResourceId"],
        "Status":
        responseStatus,
        "PhysicalResourceId":
        physicalResourceId or event.get("PhysicalResourceId"),
    }

    serialized = json.dumps(response)
    logger.info("Responding to '%s' request with: %s" %
                (event['RequestType'], serialized))

    req_data = serialized.encode('utf-8')
    logging.debug("Response:\n" + req_data)
    headers = {'content-type': '', 'content-length': str(len(req_data))}
    try:
        response = requests.put(event['ResponseURL'],
                                data=req_data,
                                headers=headers)
        logger.info("Status code: " + response.reason)
    except Exception as e:
        logger.error("Callback to CFN API failed with {}".format(e))


def add_bucket_notification(bucket_name, notification_ids, functions_arn,
                            suffixes):
    def lambda_function_configuration(notification_id, function_arn, suffix):
        return {
            'Id': notification_id,
            'LambdaFunctionArn': function_arn,
            'Events': ['s3:ObjectCreated:*'],
            "Filter": {
                "Key": {
                    "FilterRules": [{
                        "Name": "suffix",
                        "Value": suffix
                    }]
                }
            }
        }

    lambda_function_configurations = list(
        starmap(lambda_function_configuration,
                zip(notification_ids, functions_arn, suffixes)))
    logger.debug(
        "Lambda configurations: {}".format(lambda_function_configurations))
    notification_response = S3.put_bucket_notification_configuration(
        Bucket=bucket_name,
        NotificationConfiguration={
            'LambdaFunctionConfigurations': lambda_function_configurations
        })
    return notification_response


def create(properties, physical_id):
    bucket_name = properties['S3Bucket']
    suffixes = properties['Suffixes']
    notification_ids = properties['NotificationIds']
    functions_arn = properties['FunctionsARN']
    logger.debug("Create physical id {} with properties: {}".format(
        physical_id, properties))
    response = add_bucket_notification(bucket_name, notification_ids,
                                       functions_arn, suffixes)
    logger.info('AddBucketNotification response: %s' % json.dumps(response))
    return SUCCESS, physical_id


def update(properties, physical_id):
    return SUCCESS, None


def delete(properties, physical_id):
    return SUCCESS, None


def handler(event, context):
    logger.info('Received event: %s' % json.dumps(event))

    status = FAILED
    new_physical_id = None

    try:
        properties = event.get('ResourceProperties')
        physical_id = event.get('PhysicalResourceId')
        event_type = event['RequestType']

        def lambda_failed(x, y):
            return FAILED, None

        actions = {'Create': create, 'Update': update, 'Delete': delete}
        process = actions.get(event_type, lambda_failed)
        status, new_physical_id = process(properties, physical_id)
        logger.info("Status: {}, new physical ID: {}".format(
            status, new_physical_id))
    except Exception as e:
        logger.error('Exception: %s' % e)
        status = FAILED
    finally:
        cfnresponse(event, context, status, new_physical_id)
