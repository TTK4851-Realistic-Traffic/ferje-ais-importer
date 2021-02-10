import json


def handler(event, context):
    print('Event')
    print(event)
    print('Context')
    print(context)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello world')
    }