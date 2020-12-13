import boto3

S3 = boto3.client('s3')


def process_event(event, context):

    for record in event.get('Records', []):
        bucket = record.get('s3', {}).get('bucket', {}).get('name')
        key = record.get('s3', {}).get('object', {}).get('key')
        obj = S3.get_object(Bucket=bucket, Key=key)
        length = len(obj["Body"].read())
        message = "I read {} bytes in the object".format(length)
        print(message)
        return {"message": message, "event": event}
