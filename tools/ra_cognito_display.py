import boto3
import os
from botocore.exceptions import ClientError, NoRegionError

def get_region():
    if 'AWS_DEFAULT_REGION' in os.environ:
        return os.environ['AWS_DEFAULT_REGION']
    session = boto3.Session()
    if session.region_name:
        return session.region_name
    try:
        region = boto3.client('ec2').meta.region_name
        if region:
            return region
    except:
        pass
    return 'us-west-2'

def get_all_regions():
    initial_region = get_region()
    ec2_client = boto3.client('ec2', region_name=initial_region)
    try:
        response = ec2_client.describe_regions()
        return [region['RegionName'] for region in response['Regions']]
    except ClientError as e:
        print(f"获取区域列表时发生错误: {e}")
        return []

def get_user_pool_id(regions):
    for region in regions:
        cf_client = boto3.client('cloudformation', region_name=region)
        try:
            paginator = cf_client.get_paginator('list_stacks')
            for page in paginator.paginate(StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE']):
                for stack in page['StackSummaries']:
                    if 'BedrockChatStack' in stack['StackName']:
                        response = cf_client.describe_stacks(StackName=stack['StackName'])
                        for output in response['Stacks'][0]['Outputs']:
                            if output['OutputKey'].startswith('AuthUserPoolId'):
                                return output['OutputValue'], region
        except ClientError as e:
            print(f"在区域 {region} 检查堆栈时发生错误: {e}")
    return None, None

def get_cognito_users(user_pool_id, region):
    cognito_client = boto3.client('cognito-idp', region_name=region)
    users = []
    pagination_token = None

    while True:
        params = {'UserPoolId': user_pool_id, 'Limit': 60}
        if pagination_token:
            params['PaginationToken'] = pagination_token
        
        response = cognito_client.list_users(**params)
        users.extend(response['Users'])
        
        pagination_token = response.get('PaginationToken')
        if not pagination_token:
            break

    return users

def get_user_groups(user_pool_id, username, region):
    cognito_client = boto3.client('cognito-idp', region_name=region)
    try:
        response = cognito_client.admin_list_groups_for_user(
            Username=username,
            UserPoolId=user_pool_id
        )
        return [group['GroupName'] for group in response['Groups']]
    except ClientError as e:
        print(f"获取用户 {username} 的群组信息时发生错误: {e}")
        return []

def get_user_email(user):
    return next((attr['Value'] for attr in user['Attributes'] if attr['Name'] == 'email'), 'No email')

def analyze_users(users, user_pool_id, region):
    total_users = len(users)
    verified_emails = sum(1 for user in users if any(attr['Name'] == 'email_verified' and attr['Value'] == 'true' for attr in user['Attributes']))
    force_change_password = sum(1 for user in users if user['UserStatus'] == 'FORCE_CHANGE_PASSWORD')
    email_domains = {}
    user_groups = {}

    for user in users:
        email = get_user_email(user)
        if email != 'No email':
            domain = email.split('@')[-1]
            email_domains[domain] = email_domains.get(domain, 0) + 1
        
        groups = get_user_groups(user_pool_id, user['Username'], region)
        user_groups[email] = groups

    return {
        'total_users': total_users,
        'verified_emails': verified_emails,
        'unverified_emails': total_users - verified_emails,
        'force_change_password': force_change_password,
        'email_domains': email_domains,
        'user_groups': user_groups
    }

def get_user_pool_groups(user_pool_id, region):
    cognito_client = boto3.client('cognito-idp', region_name=region)
    groups = []
    pagination_token = None

    try:
        while True:
            params = {'UserPoolId': user_pool_id, 'Limit': 60}
            if pagination_token:
                params['NextToken'] = pagination_token
            
            response = cognito_client.list_groups(**params)
            groups.extend(response['Groups'])
            
            pagination_token = response.get('NextToken')
            if not pagination_token:
                break

        return groups
    except ClientError as e:
        print(f"获取用户池群组时发生错误: {e}")
        return []

def main():
    print("正在扫描所有 AWS 区域...")
    regions = get_all_regions()
    if not regions:
        print("无法获取 AWS 区域列表。请检查您的 AWS 配置和权限。")
        return

    user_pool_id, region = get_user_pool_id(regions)
    
    if not user_pool_id:
        print("未找到 User Pool ID。请检查 CloudFormation 堆栈输出。")
        return

    print(f"找到 User Pool ID: {user_pool_id} 在区域 {region}")

    try:
        # 获取用户池中的所有群组
        groups = get_user_pool_groups(user_pool_id, region)
        print(f"\n用户池中的群组 (总数: {len(groups)}):")
        for group in groups:
            print(f"- {group['GroupName']}: {group.get('Description', '无描述')}")

        users = get_cognito_users(user_pool_id, region)
        analysis = analyze_users(users, user_pool_id, region)
        
        print("\nCognito 用户池分析:")
        print(f"总用户数: {analysis['total_users']}")
        print(f"已验证邮箱: {analysis['verified_emails']}")
        print(f"未验证邮箱: {analysis['unverified_emails']}")
        print(f"需要强制修改密码: {analysis['force_change_password']}")

        print("\n邮箱域名分布:")
        for domain, count in sorted(analysis['email_domains'].items(), key=lambda x: x[1], reverse=True):
            print(f"{domain}: {count}")

        print("\n用户群组分布:")
        group_distribution = {}
        for email, user_groups in analysis['user_groups'].items():
            for group in user_groups:
                group_distribution[group] = group_distribution.get(group, 0) + 1
        
        for group, count in sorted(group_distribution.items(), key=lambda x: x[1], reverse=True):
            print(f"{group}: {count}")

        print("\n用户及其所属群组:")
        for email, user_groups in analysis['user_groups'].items():
            print(f"{email}: {', '.join(user_groups) if user_groups else '无群组'}")

    except ClientError as e:
        print(f"访问 Cognito 用户池时发生错误: {e}")

if __name__ == "__main__":
    main()    