import boto3
from botocore.exceptions import ClientError
import json

AWS_REGION = "us-west-2"
STACK_NAME = "BedrockChatStack"

# 初始化 AWS 客户端
cf = boto3.client('cloudformation', region_name=AWS_REGION)
dynamodb = boto3.client('dynamodb', region_name=AWS_REGION)
ecs = boto3.client('ecs', region_name=AWS_REGION)
ec2 = boto3.client('ec2', region_name=AWS_REGION)

def get_stack_outputs():
    try:
        response = cf.describe_stacks(StackName=STACK_NAME)
        outputs = response['Stacks'][0]['Outputs']
        return {output['OutputKey']: output['OutputValue'] for output in outputs}
    except ClientError as e:
        print(f"❌ Error getting stack outputs: {e}")
        return {}

def get_stack_resources():
    try:
        response = cf.list_stack_resources(StackName=STACK_NAME)
        return response['StackResourceSummaries']
    except ClientError as e:
        print(f"❌ Error getting stack resources: {e}")
        return []

stack_outputs = get_stack_outputs()
stack_resources = get_stack_resources()

# 更新参数
TABLE_NAME = stack_outputs.get('ConversationTableName', '')
CLUSTER_NAME = next((r['PhysicalResourceId'] for r in stack_resources if r['ResourceType'] == 'AWS::ECS::Cluster'), '')
TASK_DEFINITION_NAME = next((r['PhysicalResourceId'] for r in stack_resources if r['ResourceType'] == 'AWS::ECS::TaskDefinition'), '')
CONTAINER_NAME = "Container"
SUBNET_ID = stack_outputs.get('PrivateSubnetId0', '')
SECURITY_GROUP_ID = next((r['PhysicalResourceId'] for r in stack_resources if r['ResourceType'] == 'AWS::EC2::SecurityGroup' and 'EmbeddingTaskSecurityGroup' in r['LogicalResourceId']), '')

print("Retrieved parameters:")
print(f"TABLE_NAME: {TABLE_NAME}")
print(f"CLUSTER_NAME: {CLUSTER_NAME}")
print(f"TASK_DEFINITION_NAME: {TASK_DEFINITION_NAME}")
print(f"SUBNET_ID: {SUBNET_ID}")
print(f"SECURITY_GROUP_ID: {SECURITY_GROUP_ID}")
print()

def check_dynamodb_table():
    if not TABLE_NAME:
        print("❌ DynamoDB table name is missing.")
        return
    try:
        dynamodb.describe_table(TableName=TABLE_NAME)
        print(f"✅ DynamoDB table '{TABLE_NAME}' exists and is accessible.")
    except ClientError as e:
        print(f"❌ Error with DynamoDB table '{TABLE_NAME}': {e}")

def check_ecs_cluster():
    if not CLUSTER_NAME:
        print("❌ ECS cluster name is missing.")
        return
    try:
        response = ecs.describe_clusters(clusters=[CLUSTER_NAME])
        if response['clusters']:
            print(f"✅ ECS cluster '{CLUSTER_NAME}' exists.")
        else:
            print(f"❌ ECS cluster '{CLUSTER_NAME}' does not exist.")
    except ClientError as e:
        print(f"❌ Error checking ECS cluster '{CLUSTER_NAME}': {e}")

def check_ecs_task_definition():
    if not TASK_DEFINITION_NAME:
        print("❌ ECS task definition name is missing.")
        return
    try:
        ecs.describe_task_definition(taskDefinition=TASK_DEFINITION_NAME)
        print(f"✅ ECS task definition '{TASK_DEFINITION_NAME}' exists.")
    except ClientError as e:
        print(f"❌ Error with ECS task definition '{TASK_DEFINITION_NAME}': {e}")

def check_subnet():
    if not SUBNET_ID:
        print("❌ Subnet ID is missing.")
        return
    try:
        ec2.describe_subnets(SubnetIds=[SUBNET_ID])
        print(f"✅ Subnet '{SUBNET_ID}' exists.")
    except ClientError as e:
        print(f"❌ Error checking subnet '{SUBNET_ID}': {e}")

def check_security_group():
    if not SECURITY_GROUP_ID:
        print("❌ Security group ID is missing.")
        return
    try:
        ec2.describe_security_groups(GroupIds=[SECURITY_GROUP_ID])
        print(f"✅ Security group '{SECURITY_GROUP_ID}' exists.")
    except ClientError as e:
        print(f"❌ Error checking security group '{SECURITY_GROUP_ID}': {e}")

def simulate_dynamodb_scan():
    if not TABLE_NAME:
        print("❌ Cannot simulate DynamoDB scan: Table name is missing.")
        return
    try:
        response = dynamodb.scan(
            TableName=TABLE_NAME,
            FilterExpression="contains(SK, :substring)",
            ExpressionAttributeValues={":substring": {"S": "#BOT#"}},
            Limit=1  # 只获取一个项目来模拟
        )
        if 'Items' in response and len(response['Items']) > 0:
            print("✅ Successfully simulated DynamoDB scan. Found items matching the filter.")
        else:
            print("ℹ️ Simulated DynamoDB scan completed, but no matching items found.")
    except ClientError as e:
        print(f"❌ Error simulating DynamoDB scan: {e}")

def simulate_ecs_task_run():
    if not TASK_DEFINITION_NAME:
        print("❌ Cannot simulate ECS task run: Task definition name is missing.")
        return
    try:
        # 模拟 ECS 任务运行，但不实际启动任务
        ecs.describe_task_definition(taskDefinition=TASK_DEFINITION_NAME)
        print("✅ Successfully simulated ECS task run. Task definition is valid.")
    except ClientError as e:
        print(f"❌ Error simulating ECS task run: {e}")

def main():
    print("Checking resources and permissions:")
    check_dynamodb_table()
    check_ecs_cluster()
    check_ecs_task_definition()
    check_subnet()
    check_security_group()
    
    print("\nSimulating operations:")
    simulate_dynamodb_scan()
    simulate_ecs_task_run()

if __name__ == "__main__":
    main()