resource "aws_iam_role" "refresh" {
  name = local.function_name
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })

  inline_policy {
    name = "refresh"

    policy = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Action = [
            "logs:CreateLogStream",
            "logs:PutLogEvents"
          ]
          Effect = "Allow"
          Resource = [
            "${aws_cloudwatch_log_group.refresh.arn}:*"
          ]
        },
        {
          Action = [
            "ec2:DescribeFleets",
            "ec2:DescribeInstances"
          ]
          Resource = "*"
          Effect   = "Allow"
        },
        {
          Action = [
            "ec2:DescribeFleetInstances"
          ]
          Effect   = "Allow"
          Resource = var.fleet_arn
        },
        {
          Action = [
            "ec2:TerminateInstances"
          ]
          Effect   = "Allow"
          Resource = "*"
          Condition = {
            "StringEquals" : {
              "aws:ResourceTag/aws:ec2:fleet-id" : local.fleet_id
            }
          }
        }
      ]
    })
  }
}
