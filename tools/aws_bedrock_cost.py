import subprocess
import json
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import sys
from collections import defaultdict

def run_aws_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing AWS CLI command: {e}")
        print(f"Error output: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None

def get_date_range(period):
    today = date.today()
    if period == "":
        # 当前月
        start_date = date(today.year, today.month, 1)
        end_date = today + timedelta(days=1)  # 使用下一天作为结束日期
    elif period.startswith("P"):
        try:
            months_back = int(period[1:])
            target_month = today - relativedelta(months=months_back)
            start_date = date(target_month.year, target_month.month, 1)
            end_date = start_date + relativedelta(months=1)
        except ValueError:
            print("Invalid period format. Use 'P1' for last month, 'P2' for two months ago, etc.")
            sys.exit(1)
    else:
        print("Invalid argument. Use 'P1' for last month, 'P2' for two months ago, or no argument for current month.")
        sys.exit(1)
    
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

def get_ec2_details(start_date, end_date):
    cmd = [
        'aws', 'ce', 'get-cost-and-usage',
        '--time-period', f'Start={start_date},End={end_date}',
        '--granularity', 'MONTHLY',
        '--metrics', 'UnblendedCost',
        '--filter', '{"Dimensions": {"Key": "SERVICE", "Values": ["Amazon Elastic Compute Cloud - Compute", "EC2 - Other", "Amazon Elastic File System", "Amazon Virtual Private Cloud"]}}',
        '--group-by', 'Type=DIMENSION,Key=USAGE_TYPE'
    ]
    data = run_aws_command(cmd)
    if data and data['ResultsByTime']:
        ec2_details = defaultdict(float)
        for group in data['ResultsByTime'][0]['Groups']:
            usage_type = group['Keys'][0]
            cost = float(group['Metrics']['UnblendedCost']['Amount'])
            if 'NatGateway' in usage_type:
                ec2_details['NAT Gateway'] += cost
            elif 'DataTransfer' in usage_type:
                ec2_details['Data Transfer'] += cost
            elif 'EBS' in usage_type:
                ec2_details['EBS'] += cost
            elif any(instance_type in usage_type for instance_type in ['BoxUsage', 'DedicatedUsage']):
                ec2_details['Compute Instances'] += cost
            elif 'ElasticFileSystem' in usage_type:
                ec2_details['Elastic File System'] += cost
            elif 'VpcEndpoint' in usage_type:
                ec2_details['VPC Endpoints'] += cost
            else:
                ec2_details['Other'] += cost
        return ec2_details
    return None

# 获取命令行参数
period = sys.argv[1] if len(sys.argv) > 1 else ""

# 获取日期范围
start_date, end_date = get_date_range(period)

print(f"查询费用的时间段 (Cost Query Period): {start_date} 到 {end_date}")

# 构建AWS CLI命令，查询所有服务
cmd = [
    'aws', 'ce', 'get-cost-and-usage',
    '--time-period', f'Start={start_date},End={end_date}',
    '--granularity', 'MONTHLY',
    '--metrics', 'UnblendedCost',
    '--group-by', 'Type=DIMENSION,Key=SERVICE'
]

# 执行AWS CLI命令
data = run_aws_command(cmd)

if data:
    try:
        # 计算总费用
        total_cost = sum(float(group['Metrics']['UnblendedCost']['Amount']) 
                         for group in data['ResultsByTime'][0]['Groups'])

        # 获取各服务的费用
        service_costs = [
            (group['Keys'][0], float(group['Metrics']['UnblendedCost']['Amount']))
            for group in data['ResultsByTime'][0]['Groups']
        ]

        # 计算 Bedrock 相关费用
        bedrock_services = [s for s in service_costs if 'Bedrock' in s[0] or 'Claude' in s[0] or 'Cohere' in s[0]]
        bedrock_cost = sum(cost for _, cost in bedrock_services)

        # 从原列表中移除 Bedrock 相关服务，并添加合并后的 Bedrock 费用
        service_costs = [s for s in service_costs if s not in bedrock_services]
        service_costs.append(("Amazon Bedrock 相关费用 (Amazon Bedrock Related Costs)", bedrock_cost))

        # 修改 EC2 的描述
        service_costs = [("Elastic Compute Cloud" if s in ["EC2 - Other", "Amazon Elastic Compute Cloud - Compute"] else s, c) for s, c in service_costs]

        # 按费用降序排序
        service_costs.sort(key=lambda x: x[1], reverse=True)

        # 输出结果
        print(f"总费用 (Total Cost): ${total_cost:.2f}")
        print("\n费用最高的前5项服务 (Top 5 Services by Cost):")
        for service, cost in service_costs[:5]:
            print(f"{service}: ${cost:.2f}")

        # 获取 EC2 详细信息并生成 Note
        ec2_details = get_ec2_details(start_date, end_date)
        if ec2_details:
            print("\nNote: Elastic Compute Cloud 费用包括:")
            for service, cost in sorted(ec2_details.items(), key=lambda x: x[1], reverse=True):
                if cost > 0:
                    print(f"- {service}: ${cost:.2f}")
        else:
            print("\nNote: 无法获取 Elastic Compute Cloud 的详细费用信息。")

        # 如果Bedrock有使用，获取详细信息
        if bedrock_cost > 0:
            print("\nBedrock 使用详情 (Bedrock Usage Details):")
            for service, cost in bedrock_services:
                if cost > 0:  # 只显示费用大于0的服务
                    print(f"{service}: ${cost:.2f}")
        else:
            print("\n在此期间没有 Amazon Bedrock 的使用记录。")
            print("(No usage records for Amazon Bedrock during this period.)")

    except KeyError as e:
        print(f"Error accessing data: {e}")
        print("The structure of the returned data may be different than expected.")
else:print("Failed to retrieve cost data.")