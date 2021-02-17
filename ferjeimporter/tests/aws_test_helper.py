from dataclasses import dataclass
from typing import List


@dataclass
class S3BucketFile:
    object_key: str
    content: any = ''


def s3_event_bucket_uploaded(files: List[S3BucketFile]):
    bucket_name: str = 'my-test-bucket'
    records = []

    for file in files:
        records.append({
            's3': {
                's3SchemaVersion': '1.0',
                'bucket': {
                    'name': bucket_name,
                    'ownerIdentity': {
                        'principalId': 'EXAMPLE'
                    },
                    'arn': 'arn:aws:s3:::example-bucket'
                },
                'object': {
                    'key': file.object_key,
                    'size': 1024,
                    'eTag': '0123456789abcdef0123456789abcdef',
                    'sequencer': '0A1B2C3D4E5F678901'
                }
            }
        })

    return {
        'Records': records,
    }
