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
    data_filename= event['Records'][0]['s3']['object']['key']
    bucket = event['Records'][0]['s3']['bucket']['name']
    meta_filename=data_filename.replace('.csv', '') + '_shipdata.csv'

    if meta_filename.endswith('_shipdata.csv') == '_shipdata.csv':
        print('Sucsess')
    print(data_filename)
    print(meta_filename)
    print(bucket)
    print(f'File uploaded to bucket: {bucket} -> {filename}. Parsing...')

    data = s3.get_object(Bucket=bucket, Key=data_filename)
    metadata= s3.get_object(Bucket=bucket, Key=meta_filename)
    print(data)
    print(metadata)
    signals= data['Body'].read()
    shipinformation= metadata['Body'].read()

    print(signals)
    print(shipinformation)


    queue_url = os.environ.get('SQS_QUEUE_URL', '<No SQS_QUEUE_URL is set in this environment!>')
    print(f'Writing to SQS: {queue_url}...')
    sqs.send_message(filter_and_clean_ais_items(signals, shipinformation))
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