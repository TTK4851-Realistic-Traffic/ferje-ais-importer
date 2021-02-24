import boto3
import os
from unittest import TestCase
from moto import mock_s3, mock_sqs

from ferjeimporter.main import handler
from ferjeimporter.tests.aws_test_helper import S3BucketFile, s3_event_bucket_uploaded

TEST_S3_BUCKET_NAME = 'my-test-bucket'
dir_path = os.path.dirname(os.path.realpath(__file__))

def _read_testdata(name):
    with open(f'{dir_path}/testdata/{name}', 'r') as f:
        return f.read()


@mock_s3
@mock_sqs
class IngestAisData(TestCase):
    s3 = None

    def setUp(self) -> None:
        """
        Creates our mocked S3 bucket which ferjeimporter.main.handler will automatically connect to
        :return:
        """
        s3 = boto3.resource('s3', region_name='us-east-1')
        s3.create_bucket(Bucket=TEST_S3_BUCKET_NAME)

        self.s3 = boto3.client('s3', region_name='us-east-1')

    def test_import_success(self):
        """
        Verifies that uploaded files are processed correctly
        and removed from S3 when completed
        :return:
        """
        # Files we are using in this test
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

        # Run our event handler
        handler(event, {})

        # Assert the outcome is correct
        objects_in_s3 = {content['Key'] for content in self.s3.list_objects_v2(Bucket=TEST_S3_BUCKET_NAME)['Contents']}

        # TODO This will correctly fail, because handler has not been correctly imported yet
        # All processed files should have been deleted from S3
        for file in uploaded_files:
            self.assertNotIn(file.object_key, objects_in_s3)

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
