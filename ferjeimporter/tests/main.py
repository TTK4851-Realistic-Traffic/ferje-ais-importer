import boto3
from unittest import TestCase
from moto import mock_s3

from ferjeimporter.main import handler
from ferjeimporter.tests.aws_test_helper import S3BucketFile, s3_event_bucket_uploaded

TEST_S3_BUCKET_NAME = 'my-test-bucket'


def _read_testdata(name):
    with open(f'./testdata/{name}', 'r') as f:
        return f.read()


@mock_s3
class IngestAisData(TestCase):
    s3 = None

    def setUp(self) -> None:
        s3 = boto3.resource('s3', region_name='us-east-1')
        s3.create_bucket(Bucket=TEST_S3_BUCKET_NAME)

        self.s3 = boto3.client('s3', region_name='us-east-1')

    def test_import_success(self):
        # Declare the files we are using in this test
        uploaded_files = [
            S3BucketFile(
                object_key='2018-07-01.csv',
                content=_read_testdata('2018-07-01.csv'),
            ),
            S3BucketFile(
                object_key='2018-07-01_shipdata.csv',
                content=_read_testdata('2018-07-01_shipdata.csv'),
            ),
        ]

        # Upload the data to the mocked instance of S3
        for file in uploaded_files:
            self.s3.put_object(Bucket=TEST_S3_BUCKET_NAME, Key=file.object_key, Body=file.content)

        event = s3_event_bucket_uploaded(uploaded_files)
        # Run test
        handler(event, {})

    def test_import_ignores_missing_shipdata(self):
        """
        Ensures that if for example the file 2018-07-01.csv does not have 2018-07-01_shipdata.csv,
        then we ignore that file and possibly log and error to the console.
        :return:
        """
        uploaded_files = [
            S3BucketFile(
                object_key='2018-07-01.csv',
                content=_read_testdata('2018-07-01.csv'),
            ),
        ]

        for file in uploaded_files:
            self.s3.put_object(Bucket=TEST_S3_BUCKET_NAME, Key=file.object_key, Body=file.content)

        event = s3_event_bucket_uploaded(uploaded_files)
        # Run test
        handler(event, {})
