from moto import mock_s3, mock_sqs
import boto3
import os
from unittest import TestCase, mock
from botocore.exceptions import ClientError
from ferjeimporter.main import handler
from ferjeimporter.tests.aws_test_helper import S3BucketFile, s3_event_bucket_uploaded

AWS_DEFAULT_REGION = 'us-east-1'
TEST_S3_BUCKET_NAME = 'my-test-bucket'
TEST_SQS_QUEUE_NAME = 'ferje-ais-importer-test-pathtaker-source'
dir_path = os.path.dirname(os.path.realpath(__file__))


def _read_testdata(name):
    with open(f'{dir_path}/testdata/{name}', 'r') as f:
        return f.read()


@mock_s3
@mock_sqs
class IngestAisData(TestCase):
    s3 = None
    sqs = None

    def setUp(self) -> None:
        """
        Creates our mocked S3 bucket which ferjeimporter.main.handler will automatically connect to
        :return:
        """
        # Ensure test setup uses the correct test credentials
        os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
        os.environ['AWS_SECURITY_TOKEN'] = 'testing'
        os.environ['AWS_SESSION_TOKEN'] = 'testing'

        # Initialize S3 test-bucket
        s3 = boto3.resource('s3', region_name=AWS_DEFAULT_REGION)
        bucket = s3.create_bucket(Bucket=TEST_S3_BUCKET_NAME)
        # Clear the bucket
        bucket.objects.all().delete()
        self.s3 = boto3.client('s3', region_name=AWS_DEFAULT_REGION)

        # Initialize SQS test-queue
        sqs = boto3.resource('sqs', region_name=AWS_DEFAULT_REGION)
        self.queue = sqs.create_queue(QueueName=TEST_SQS_QUEUE_NAME, Attributes={'DelaySeconds': '0'})
        self.sqs = boto3.client('sqs')

        environment_patcher = mock.patch.dict(os.environ, {
            'SQS_QUEUE_URL': self.queue.url,
            # Ensure our system looks for resources in the correct region
            'AWS_DEFAULT_REGION': AWS_DEFAULT_REGION,
            # Prevent any use of non-test credentials
            'AWS_ACCESS_KEY_ID': 'testing',
            'AWS_SECRET_ACCESS_KEY': 'testing',
            'AWS_SECURITY_TOKEN': 'testing',
            'AWS_SESSION_TOKEN': 'testing',
        })
        environment_patcher.start()
        self.addCleanup(environment_patcher.stop)

    def test_import_success(self):
        """
        Verifies that uploaded files are processed correctly
        and removed from S3 when completed
        :return:
        """
        # Files we are using in this test
        uploaded_files = [
            S3BucketFile(
                object_key='2018-07-02.csv',
                content=_read_testdata('2018-07-02.csv'),
            ),
            S3BucketFile(
                object_key='2018-07-02_shipdata.csv',
                content=_read_testdata('2018-07-02_shipdata.csv'),
            ),
        ]
        # Upload the data to the mocked instance of S3
        for file in uploaded_files:
            self.s3.put_object(Bucket=TEST_S3_BUCKET_NAME, Key=file.object_key, Body=file.content)

        event = s3_event_bucket_uploaded([uploaded_files[0]])

        # Run our event handler
        handler(event, {})

        messages = self.queue.receive_messages(
            MessageAttributeNames=['All'],
            MaxNumberOfMessages=10,
            WaitTimeSeconds=2
        )

        # At least one message should have been posted to the queue
        self.assertGreaterEqual(len(messages), 1)

        list_response = self.s3.list_objects_v2(Bucket=TEST_S3_BUCKET_NAME)
        # All processed files should have been removed
        self.assertNotIn('Contents', list_response)

    def test_import_fails_on_missing_ship_metadata(self):
        """
        File of signals (yyyy-mm-dd.csv) cannot be processed without
        the correlated metadata (yyyy-mm-dd_shipdata.csv). Let the function fail to
        ensure delivery is retried later.
        :return:
        """
        uploaded_files = [
            S3BucketFile(
                object_key='2018-07-02.csv',
                content=_read_testdata('2018-07-02.csv'),
            ),
        ]

        for file in uploaded_files:
            self.s3.put_object(Bucket=TEST_S3_BUCKET_NAME, Key=file.object_key, Body=file.content)

        event = s3_event_bucket_uploaded(uploaded_files)

        self.assertRaises(ClientError, lambda: handler(event, {}))

    def test_import_ignores_non_signal_files(self):
        uploaded_files = [
            S3BucketFile(
                object_key='2018-07-02_shipdata.csv',
                content=_read_testdata('2018-07-02_shipdata.csv'),
            ),
        ]

        for file in uploaded_files:
            self.s3.put_object(Bucket=TEST_S3_BUCKET_NAME, Key=file.object_key, Body=file.content)

        event = s3_event_bucket_uploaded(uploaded_files)
        # Run our event handler
        handler(event, {})

        list_response = self.s3.list_objects_v2(Bucket=TEST_S3_BUCKET_NAME)
        self.assertIn('Contents', list_response)
        # The _shipdata.csv file should not have been removed
        for file in list_response['Contents']:
            self.assertTrue(file['Key'].endswith('_shipdata.csv'))
