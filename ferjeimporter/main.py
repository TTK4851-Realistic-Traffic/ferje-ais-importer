import json
import os
import boto3

from ferjeimporter.ais_processor import filter_and_clean_ais_items


def handler(event, context):
    """
    Triggers when objects are created in an S3 storage. Responsible for loading raw
    historical AIS information, filter any files
    :param event:
    :param context:
    :return:
    """
    # Important! This has to be initialized after mocks from moto has been set up.
    # This is the reason why we have placed the declaration inside the handler function
    s3 = boto3.client('s3')
    sqs = boto3.client('sqs')

    print(event)
    
    filename = event['Records'][0]['s3']['object']['key']
    bucket = event['Records'][0]['s3']['bucket']['name']

    print(f'File uploaded to bucket: {bucket} -> {filename}. Parsing...')

    data = s3.get_object(Bucket=bucket, Key=filename)
    contents = data['Body'].read()

    filter_and_clean_ais_items(contents, [])

    queue_url = os.environ.get('SQS_QUEUE_URL', '<No SQS_QUEUE_URL is set in this environment!>')
    print(f'Writing to SQS: {queue_url}...')
    sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=0,
        MessageBody=json.dumps(def filter_and_clean_ais_items(signals, shipinformation):)
    )
    print('Done writing!')

    # Processed files are no longer of use and can be discarded
    s3.delete_object(Bucket=bucket, Key=filename)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'file': filename,
            'bucket': bucket,
        })
    }