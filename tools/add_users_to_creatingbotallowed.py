import boto3
from botocore.exceptions import ClientError

def get_user_pool_id(region):
    cf_client = boto3.client('cloudformation', region_name=region)
    try:
        paginator = cf_client.get_paginator('list_stacks')
        for page in paginator.paginate(StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE']):
            for stack in page['StackSummaries']:
                if 'BedrockChatStack' in stack['StackName']:
                    response = cf_client.describe_stacks(StackName=stack['StackName'])
                    for output in response['Stacks'][0]['Outputs']:
                        if output['OutputKey'].startswith('AuthUserPoolId'):
                            return output['OutputValue']
    except ClientError as e:
        print(f"Error getting user pool ID: {e}")
    return None

def get_cognito_users(user_pool_id, region):
    cognito_client = boto3.client('cognito-idp', region_name=region)
    users = []
    pagination_token = None

    try:
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
    except ClientError as e:
        print(f"Error getting Cognito users: {e}")
        return []

def get_user_groups(user_pool_id, username, region):
    cognito_client = boto3.client('cognito-idp', region_name=region)
    try:
        response = cognito_client.admin_list_groups_for_user(
            Username=username,
            UserPoolId=user_pool_id
        )
        return [group['GroupName'] for group in response['Groups']]
    except ClientError as e:
        print(f"Error getting groups for user {username}: {e}")
        return []

def add_user_to_group(user_pool_id, username, group_name, region):
    cognito_client = boto3.client('cognito-idp', region_name=region)
    try:
        cognito_client.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=username,
            GroupName=group_name
        )
        print(f"Added user {username} to group {group_name}")
    except ClientError as e:
        print(f"Error adding user {username} to group {group_name}: {e}")

def main():
    region = 'us-west-2'  # 替换为您的 AWS 区域
    user_pool_id = get_user_pool_id(region)
    
    if not user_pool_id:
        print("User Pool ID not found. Please check your CloudFormation stack.")
        return

    print(f"Found User Pool ID: {user_pool_id}")

    users = get_cognito_users(user_pool_id, region)
    
    for user in users:
        username = user['Username']
        email = next((attr['Value'] for attr in user['Attributes'] if attr['Name'] == 'email'), 'No email')
        groups = get_user_groups(user_pool_id, username, region)
        
        if 'CreatingBotAllowed' not in groups:
            print(f"User {email} is not in CreatingBotAllowed group. Adding...")
            add_user_to_group(user_pool_id, username, 'CreatingBotAllowed', region)
        else:
            print(f"User {email} is already in CreatingBotAllowed group.")

if __name__ == "__main__":
    main()