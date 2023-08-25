locals {
  function_name = "${var.name_prefix}${random_id.prefix.hex}"
}

resource "random_id" "prefix" {
  byte_length = 8
}

resource "aws_cloudwatch_event_rule" "refresh" {
  name = local.function_name

  event_pattern = jsonencode({
    source      = ["aws.ec2fleet"]
    detail-type = ["EC2 Fleet State Change"]
    detail      = { "sub-type" : ["modify_succeeded"] }
    resources   = [var.fleet_arn]
  })
}

resource "aws_cloudwatch_event_target" "refresh" {
  rule      = aws_cloudwatch_event_rule.refresh.name
  arn       = aws_lambda_function.refresh.arn
  target_id = local.function_name
}

resource "aws_cloudwatch_log_group" "refresh" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = 7
}

data "archive_file" "refresh" {
  type        = "zip"
  source_file = "${path.module}/function.py"
  output_path = "function.zip"
}

resource "aws_lambda_function" "refresh" {
  function_name    = local.function_name
  role             = aws_iam_role.refresh.arn
  filename         = data.archive_file.refresh.output_path
  runtime          = "python3.10"
  handler          = "function.lambda_handler"
  timeout          = 30
  memory_size      = 128
  source_code_hash = data.archive_file.refresh.output_base64sha256
}

resource "aws_lambda_permission" "refresh" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.refresh.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.refresh.arn
}