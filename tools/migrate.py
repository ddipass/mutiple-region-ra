import json
import boto3
import logging
import time
from botocore.exceptions import ClientError

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AWS 配置
AWS_REGION = "us-west-2"
TABLE_NAME = "BedrockChatStack-DatabaseConversationTable -------------- "
CLUSTER_NAME = "BedrockChatStack-EmbeddingCluster -------------- "
TASK_DEFINITION_NAME = "arn:aws:ecs:us-west-2:----------:task-definition/BedrockChatStackEmbeddingTaskDefinition----------:4"
CONTAINER_NAME = "Container"
SUBNET_ID = "subnet-****************"
SECURITY_GROUP_ID = "sg-*****************"

# 初始化 AWS 客户端
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(TABLE_NAME)
ecs = boto3.client("ecs", region_name=AWS_REGION)
s3 = boto3.client("s3", region_name=AWS_REGION)

def create_s3_bucket():
    """创建 S3 桶用于存储备份"""
    bucket_name = f"bedrockchat-backup-{int(time.time())}"
    try:
        s3.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': AWS_REGION}
        )
        logger.info(f"Created S3 bucket: {bucket_name}")
        return bucket_name
    except ClientError as e:
        logger.error(f"Failed to create S3 bucket: {e}")
        raise

def create_backup(backup_bucket):
    """创建 DynamoDB 表的备份并导出到 S3"""
    try:
        backup_name = f"{TABLE_NAME}-backup-{int(time.time())}"
        response = dynamodb.meta.client.create_backup(
            TableName=TABLE_NAME,
            BackupName=backup_name
        )
        backup_arn = response['BackupDetails']['BackupArn']
        logger.info(f"Created backup: {backup_name}")

        # 导出备份到 S3
        export_name = f"export-{backup_name}"
        dynamodb.meta.client.export_table_to_point_in_time(
            TableArn=table.table_arn,
            S3Bucket=backup_bucket,
            S3Prefix=export_name,
            ExportTime=response['BackupDetails']['BackupCreationDateTime'],
            ExportFormat='DYNAMODB_JSON'
        )
        logger.info(f"Initiated export of backup to S3: s3://{backup_bucket}/{export_name}")
        
        return backup_arn, f"s3://{backup_bucket}/{export_name}"
    except ClientError as e:
        logger.error(f"Failed to create or export backup: {e}")
        raise

def process_items(items, is_test=False):
    """处理项目并启动 ECS 任务"""
    for item in items:
        try:
            pk = item['PK']
            sk = item['SK']
            payload = {
                "Keys": {
                    "PK": {"S": pk},
                    "SK": {"S": sk},
                },
            }
            
            if not is_test:
                response = ecs.run_task(
                    cluster=CLUSTER_NAME,
                    launchType="FARGATE",
                    taskDefinition=TASK_DEFINITION_NAME,
                    networkConfiguration={
                        "awsvpcConfiguration": {
                            "subnets": [SUBNET_ID],
                            "securityGroups": [SECURITY_GROUP_ID],
                            "assignPublicIp": "ENABLED",
                        }
                    },
                    overrides={
                        "containerOverrides": [
                            {
                                "name": CONTAINER_NAME,
                                "command": [
                                    "-u",
                                    "embedding/main.py",
                                    json.dumps(payload["Keys"]),
                                ],
                            }
                        ]
                    },
                )
                logger.info(f"Started embed task for bot: {sk}")
            else:
                logger.info(f"Test mode: Would start embed task for bot: {sk}")
        except ClientError as e:
            logger.error(f"Error processing item {sk}: {e}")

def main(test_mode=False, limit=None):
    """主函数"""
    try:
        # 创建 S3 桶
        backup_bucket = create_s3_bucket()
        logger.info(f"Created S3 bucket for backups: {backup_bucket}")

        # 创建备份并导出到 S3
        backup_arn, export_location = create_backup(backup_bucket)
        logger.info(f"Backup created with ARN: {backup_arn}")
        logger.info(f"Backup exported to: {export_location}")

        scan_kwargs = {
            "FilterExpression": "contains(SK, :substring)",
            "ExpressionAttributeValues": {":substring": "#BOT#"},
        }

        if limit:
            scan_kwargs["Limit"] = limit

        while True:
            response = table.scan(**scan_kwargs)
            items = response.get("Items", [])

            if not items:
                logger.info("No more items to process.")
                break

            logger.info(f"Processing {len(items)} items...")
            process_items(items, is_test=test_mode)

            if "LastEvaluatedKey" not in response:
                break
            scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

        logger.info("Migration completed successfully.")
    except Exception as e:
        logger.error(f"An error occurred during migration: {e}")
        logger.info(f"You can find the backup at: {export_location}")

if __name__ == "__main__":
    # 运行测试模式，只处理前 10 个项目
    main(test_mode=True, limit=10)
    
    # 询问用户是否继续完整迁移
    user_input = input("Do you want to proceed with the full migration? (y/N): ")
    if user_input.lower() == 'y':
        main(test_mode=False)
    else:
        logger.info("Full migration cancelled by user.")