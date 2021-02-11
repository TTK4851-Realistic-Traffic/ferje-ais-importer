import json
import boto3

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
    print('Contents from file')
    print(contents)
    return {
        'statusCode': 200,
        'body': json.dumps({
            'file': filename,
            'bucket': bucket,
        })
    }