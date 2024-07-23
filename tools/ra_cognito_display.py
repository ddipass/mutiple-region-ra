import boto3
from botocore.exceptions import ClientError

def get_all_regions():
    ec2_client = boto3.client('ec2')
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

def analyze_users(users):
    total_users = len(users)
    verified_emails = sum(1 for user in users if any(attr['Name'] == 'email_verified' and attr['Value'] == 'true' for attr in user['Attributes']))
    force_change_password = sum(1 for user in users if user['UserStatus'] == 'FORCE_CHANGE_PASSWORD')
    email_domains = {}

    for user in users:
        email = next((attr['Value'] for attr in user['Attributes'] if attr['Name'] == 'email'), None)
        if email:
            domain = email.split('@')[-1]
            email_domains[domain] = email_domains.get(domain, 0) + 1

    return {
        'total_users': total_users,
        'verified_emails': verified_emails,
        'unverified_emails': total_users - verified_emails,
        'force_change_password': force_change_password,
        'email_domains': email_domains
    }

def main():
    print("正在扫描所有 AWS 区域...")
    regions = get_all_regions()
    user_pool_id, region = get_user_pool_id(regions)
    
    if not user_pool_id:
        print("未找到 User Pool ID。请检查 CloudFormation 堆栈输出。")
        return

    print(f"找到 User Pool ID: {user_pool_id} 在区域 {region}")

    try:
        users = get_cognito_users(user_pool_id, region)
        analysis = analyze_users(users)
        
        print("\nCognito 用户池分析:")
        print(f"总用户数: {analysis['total_users']}")
        print(f"已验证邮箱: {analysis['verified_emails']}")
        print(f"未验证邮箱: {analysis['unverified_emails']}")
        print(f"需要强制修改密码: {analysis['force_change_password']}")

        print("\n邮箱域名分布:")
        for domain, count in sorted(analysis['email_domains'].items(), key=lambda x: x[1], reverse=True):
            print(f"{domain}: {count}")

    except ClientError as e:
        print(f"访问 Cognito 用户池时发生错误: {e}")

if __name__ == "__main__":
    main()