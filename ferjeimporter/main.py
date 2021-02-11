import json
import boto3

from ais_processor import filter_and_clean_ais_items

s3 = boto3.client('s3')


def handler(event, context):
    """
    Triggers when objects are created in an S3 storage. Responsible for loading raw
    historical AIS information, filter any files
    :param event:
    :param context:
    :return:
    """
    filename = event['Records'][0]['s3']['object']['key']
    bucket = event['Records'][0]['s3']['bucket']['name']

    print(f'File uploaded to bucket: {bucket} -> {filename}. Parsing...')

    data = s3.get_object(Bucket=bucket, Key=filename)
    contents = data['Body'].read()

    filter_and_clean_ais_items(contents)

    # Processed files are no longer of use and can be discarded
    s3.delete_object(Bucket=bucket, Key=filename)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'file': filename,
            'bucket': bucket,
        })
    }