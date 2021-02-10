terraform {
  required_version = "0.13.2"

  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "3.27.0"
    }
  }
}

provider "aws" {
  # Configuration options
  region = "us-east-1"
}

locals {
  application_name = "ferje-ais-importer"
  environment = "prod"

  qualified_name = "${local.application_name}-${local.environment}"
  tags = {
    "managedBy" = "terraform"
    "application" = local.application_name
    "environment" = local.environment
    "ntnuCourse" = "ttk4851"
  }
}

resource "aws_iam_role" "iam_for_lambda" {
  name = "${local.qualified_name}-role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF

  tags = local.tags
}

data "archive_file" "source" {
  type        = "zip"
  source_dir = "../../ferjeimporter"
  output_path = "../../out.zip"
}


# This is to optionally manage the CloudWatch Log Group for the Lambda Function.
# If skipping this resource configuration, also add "logs:CreateLogGroup" to the IAM policy below.
resource "aws_cloudwatch_log_group" "logs" {
  name              = "/aws/lambda/${local.qualified_name}"
  retention_in_days = 7
}

# See also the following AWS managed policy: AWSLambdaBasicExecutionRole
resource "aws_iam_policy" "lambda_logging" {
  name        = "${local.qualified_name}-lambda-logging"
  path        = "/"
  description = "IAM policy for logging from a lambda"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*",
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = aws_iam_policy.lambda_logging.arn
}

resource "aws_lambda_function" "ferjeaisimporter" {
  filename      = data.archive_file.source.output_path
  function_name = local.qualified_name
  role          = aws_iam_role.iam_for_lambda.arn
  # This has to match the filename and function name in ../../ferjeimporter/main.py
  # That is to be executed
  handler       = "main.handler"

  # The filebase64sha256() function is available in Terraform 0.11.12 and later
  # For Terraform 0.11.11 and earlier, use the base64sha256() function and the file() function:
  # source_code_hash = "${base64sha256(file("lambda_function_payload.zip"))}"
  source_code_hash = data.archive_file.source.output_base64sha256

  runtime = "python3.8"

  tags = local.tags

  environment {
    variables = {
      foo = "bar"
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_logs,
    aws_cloudwatch_log_group.logs,
  ]
}

resource "aws_s3_bucket" "ais_raw_files" {
  bucket = "${local.qualified_name}-ais-raw"
}

resource "aws_lambda_permission" "allow_bucket_to_trigger_lambda" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ferjeaisimporter.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.ais_raw_files.arn
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.ais_raw_files.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.ferjeaisimporter.arn
    events              = ["s3:ObjectCreated:*"]
//    filter_prefix       = "AWSLogs/"
    filter_suffix       = ".csv"
  }

  depends_on = [aws_lambda_permission.allow_bucket_to_trigger_lambda]
}