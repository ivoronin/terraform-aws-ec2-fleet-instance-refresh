# terraform-aws-ec2-fleet-instance-refresh
Sets up a watchdog to refresh instances in EC2 Fleet when fleet's launch template version is updated

## How it works
A Lambda function runs on `EC2 Fleet State Change` EventBridge event and terminates all ec2 instances in the changed fleet, which `aws:ec2launchtemplate:version` tag's value doesn't match the one set in the fleet's launch template.

## Variables

- `name_prefix` - name prefix to use when creating required resources
- `fleet_arn` - target EC2 Fleet ARN

## Example

```hcl
module "fleet_refresh" {
  source  = "ivoronin/ec2-fleet-instance-refresh/aws"

  name_prefix = "my-prefix-"
  fleet_arn   = aws_ec2_fleet.app.arn
}
```