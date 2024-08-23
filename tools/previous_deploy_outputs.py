import sys
import subprocess
import importlib
import os

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# 检查并安装所需的库
required_packages = ['boto3', 'tabulate']
for package in required_packages:
    try:
        importlib.import_module(package)
    except ImportError:
        print(f"{package} 未安装。正在安装...")
        install(package)
        print(f"{package} 安装完成。")

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from tabulate import tabulate

# ANSI 颜色代码
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def color_print(text, color):
    print(f"{color}{text}{Colors.ENDC}")

def get_default_region():
    """获取默认 AWS 区域"""
    region = os.environ.get('AWS_DEFAULT_REGION')
    if not region:
        session = boto3.Session()
        region = session.region_name
    if not region:
        region = 'us-west-2'  # 设置一个默认区域
    return region

def get_all_regions():
    default_region = get_default_region()
    ec2_client = boto3.client('ec2', region_name=default_region)
    try:
        response = ec2_client.describe_regions()
        return [region['RegionName'] for region in response['Regions']]
    except ClientError as e:
        color_print(f"获取区域列表时发生错误: {e}", Colors.RED)
        return []

def get_cloudformation_stacks(stack_name_contains):
    all_regions = get_all_regions()
    stacks_info = []

    for region in all_regions:
        color_print(f"\n正在检查区域: {region}", Colors.BLUE)
        stacks_info.extend(check_region(region, stack_name_contains))

    return stacks_info

def check_region(region, stack_name_contains):
    cf_client = boto3.client('cloudformation', region_name=region)
    stacks_info = []

    try:
        paginator = cf_client.get_paginator('list_stacks')
        for page in paginator.paginate(StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE']):
            for stack in page['StackSummaries']:
                if stack_name_contains.lower() in stack['StackName'].lower():
                    color_print(f"在 {region} 找到匹配的堆栈: {stack['StackName']}", Colors.GREEN)
                    stack_details = cf_client.describe_stacks(StackName=stack['StackName'])['Stacks'][0]
                    outputs = stack_details.get('Outputs', [])
                    stacks_info.append({
                        'Region': region,
                        'StackName': stack['StackName'],
                        'Outputs': outputs
                    })
    except ClientError as e:
        color_print(f"在区域 {region} 检查堆栈时发生错误: {e}", Colors.RED)

    return stacks_info

def print_stack_outputs(stacks_info):
    for stack in stacks_info:
        color_print(f"\n区域: {stack['Region']}", Colors.BLUE)
        color_print(f"堆栈名称: {stack['StackName']}", Colors.GREEN)
        if stack['Outputs']:
            print_colored_table(stack['Outputs'])
        else:
            color_print("该堆栈没有输出。", Colors.YELLOW)

def print_colored_table(outputs):
    headers = ["Key", "Value"]
    table_data = []
    migrate_keys = [
        "DatabaseConversationTableName",
        "EmbeddingClusterName",
        "EmbeddingTaskDefinitionName",
        "PrivateSubnetId0",
        "EmbeddingTaskSecurityGroupId"
    ]
    for output in outputs:
        key = output['OutputKey']
        value = output['OutputValue']
        if any(migrate_key in key for migrate_key in migrate_keys):
            key = f"{Colors.MAGENTA}{key}{Colors.ENDC}"
            value = f"{Colors.MAGENTA}{value}{Colors.ENDC}"
        else:
            key = f"{Colors.YELLOW}{key}{Colors.ENDC}"
            value = f"{Colors.CYAN}{value}{Colors.ENDC}"
        table_data.append([key, value])
    
    print(tabulate(table_data, headers=headers, tablefmt="simple"))

# 主程序
if __name__ == "__main__":
    stack_name_contains = 'BedrockChatStack'
    stacks_info = get_cloudformation_stacks(stack_name_contains)

    if stacks_info:
        color_print(f"\n找到 {len(stacks_info)} 个包含 '{stack_name_contains}' 的堆栈:", Colors.BOLD)
        print_stack_outputs(stacks_info)
        color_print("\n注意: 紫色标记的参数是 migrate.py 所需的信息。", Colors.BOLD)
    else:
        color_print(f"\n在所有区域中都没有找到包含 '{stack_name_contains}' 的堆栈。", Colors.RED)
        color_print("请检查以下几点:", Colors.YELLOW)
        color_print("1. 确保您的AWS凭证配置正确且有足够的权限。", Colors.YELLOW)
        color_print("2. 检查堆栈名称是否正确。", Colors.YELLOW)
        color_print("3. 确认堆栈状态是否为 CREATE_COMPLETE, UPDATE_COMPLETE 或 UPDATE_ROLLBACK_COMPLETE。", Colors.YELLOW)