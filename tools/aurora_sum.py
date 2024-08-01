import boto3
import urllib.parse
from botocore.exceptions import ClientError, NoRegionError

# ANSI color codes
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
ENDC = '\033[0m'

def get_region():
    """
    尝试多种方法获取 AWS 区域
    """
    session = boto3.Session()
    if session.region_name:
        return session.region_name
    
    # 如果 Session 没有区域信息，尝试从 EC2 实例元数据获取
    try:
        region = boto3.client('ec2').meta.region_name
        if region:
            return region
    except:
        pass
    
    # 如果以上方法都失败，使用一个默认区域
    return 'us-west-2'  # 您可以更改为任何适合的默认区域

def get_aurora_clusters(region):
    rds = boto3.client('rds', region_name=region)
    clusters = []
    
    try:
        paginator = rds.get_paginator('describe_db_clusters')
        for page in paginator.paginate():
            clusters.extend(page['DBClusters'])
    except ClientError as e:
        print(f"{RED}Error getting Aurora clusters: {e}{ENDC}")
    
    return clusters

def get_vector_database_info(cluster, region):
    rds = boto3.client('rds', region_name=region)
    vector_dbs = []
    
    instances = cluster.get('DBClusterMembers', [])
    
    for instance in instances:
        instance_id = instance['DBInstanceIdentifier']
        try:
            response = rds.describe_db_instances(DBInstanceIdentifier=instance_id)
            db_instance = response['DBInstances'][0]
            
            if 'vector' in instance_id.lower():
                vector_dbs.append({
                    'id': instance_id,
                    'size': db_instance['AllocatedStorage'],  # Size in GB
                    'engine': db_instance['Engine'],
                    'engine_version': db_instance['EngineVersion']
                })
        except ClientError as e:
            print(f"{RED}Error getting info for instance {instance_id}: {e}{ENDC}")
    
    return vector_dbs

def get_aws_console_link(cluster_id, region):
    base_url = "https://console.aws.amazon.com/rds/home"
    params = {
        "region": region,
        "#database:id": cluster_id,
        "tab": "connectivity"
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"

def main():
    region = get_region()
    print(f"{YELLOW}Using AWS region: {region}{ENDC}")
    
    try:
        clusters = get_aurora_clusters(region)
        total_vector_dbs = 0
        affected_clusters = 0
        
        print(f"\n{YELLOW}Aurora集群向量数据库统计:{ENDC}")
        print("=" * 80)
        
        for cluster in clusters:
            vector_dbs = get_vector_database_info(cluster, region)
            if vector_dbs:
                print(f"{GREEN}集群:{ENDC} {cluster['DBClusterIdentifier']}")
                print(f"{GREEN}AWS Console 链接:{ENDC} {BLUE}{get_aws_console_link(cluster['DBClusterIdentifier'], region)}{ENDC}")
                for db in vector_dbs:
                    print(f"  {GREEN}向量数据库:{ENDC} {db['id']}")
                    print(f"    {GREEN}大小:{ENDC} {db['size']} GB")
                    print(f"    {GREEN}引擎:{ENDC} {db['engine']} {db['engine_version']}")
                print("-" * 80)
                total_vector_dbs += len(vector_dbs)
                affected_clusters += 1
        
        print(f"\n{YELLOW}总结:{ENDC}")
        print(f"{GREEN}受影响的Aurora集群数量:{ENDC} {affected_clusters}")
        print(f"{GREEN}总向量数据库数量:{ENDC} {total_vector_dbs}")
    
    except NoRegionError:
        print(f"{RED}Error: No AWS region specified. Please set your AWS region.{ENDC}")
    except ClientError as e:
        print(f"{RED}AWS API Error: {e}{ENDC}")
    except Exception as e:
        print(f"{RED}Unexpected error: {e}{ENDC}")

if __name__ == "__main__":
    main()