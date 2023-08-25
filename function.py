import logging
import boto3
import json

logging.getLogger().setLevel(logging.INFO)

ec2 = boto3.client("ec2")


class Status:
    @classmethod
    def error(cls, msg):
        logging.error(msg)
        return json.dumps({"status": "error", "message": msg})

    @classmethod
    def ok(cls, msg):
        return json.dumps({"status": "ok", "message": msg})


def get_fleet_instance_ids(fleet_id):
    r = ec2.describe_fleet_instances(FleetId=fleet_id)
    for r in r["ActiveInstances"]:
        yield r["InstanceId"]


def get_fleet_launch_tpl_specs(fleet_id):
    r = ec2.describe_fleets(FleetIds=[fleet_id])
    fleet = r["Fleets"][0]
    for c in fleet["LaunchTemplateConfigs"]:
        yield c["LaunchTemplateSpecification"]


def get_instances(instance_ids):
    result = ec2.describe_instances(InstanceIds=instance_ids)
    for r in result["Reservations"]:
        yield from r["Instances"]


def refresh_fleet_instances(fleet_id):
    tpl_specs = list(get_fleet_launch_tpl_specs(fleet_id))
    spec_tpl_versions = {t["LaunchTemplateId"]: t["Version"] for t in tpl_specs}

    logging.info(
        "fleet %s: running templates: %s",
        fleet_id,
        ", ".join(f"{k}:{v}" for k, v in spec_tpl_versions.items()),
    )

    fleet_inst_ids = list(get_fleet_instance_ids(fleet_id))
    num_refreshed_instances = 0

    for inst in get_instances(fleet_inst_ids):
        inst_id = inst["InstanceId"]
        inst_state = inst["State"]["Name"]
        if inst_state != "running":
            logging.info("instance %s: not running, skipping", inst_id)
            continue

        tags = {t["Key"]: t["Value"] for t in inst["Tags"]}
        inst_tpl_id = tags["aws:ec2launchtemplate:id"]
        inst_tpl_ver = tags["aws:ec2launchtemplate:version"]

        if inst_tpl_id not in spec_tpl_versions:
            logging.warning(
                "instance %s: running unexpected template %s:%s, skipping",
                inst_id,
                inst_tpl_id,
                inst_tpl_ver,
            )
            continue

        spec_tpl_ver = spec_tpl_versions[inst_tpl_id]

        if inst_tpl_ver != spec_tpl_ver:
            logging.info(
                "instance %s: running wrong template version %s:%s, terminating",
                inst_id,
                inst_tpl_id,
                inst_tpl_ver,
            )
            ec2.terminate_instances(InstanceIds=[inst_id])
            num_refreshed_instances += 1
        else:
            logging.info(
                "instance %s: running correct template version %s:%s, skipping",
                inst_id,
                inst_tpl_id,
                inst_tpl_ver,
            )
            continue

    return Status.ok(f"refreshed {num_refreshed_instances} instances")


def lambda_handler(event, context):
    # Validate event
    if "resources" not in event or len(event["resources"]) != 1:
        return Status.error(f"invalid event: {event}")

    fleet_arn = event["resources"][0]

    # Validate fleet ARN
    p = fleet_arn.split("/")
    if len(p) != 2:
        return Status.error(f"invalid fleet ARN: {fleet_arn}")

    fleet_id = p[1]

    try:
        return refresh_fleet_instances(fleet_id)
    except Exception as e:
        return Status.error(f"error refreshing fleet {fleet_id}: {e}")
