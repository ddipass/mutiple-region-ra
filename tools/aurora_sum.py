import boto3
import urllib.parse

# ANSI color codes
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
ENDC = '\033[0m'

def get_aurora_clusters():
    rds = boto3.client('rds')
    clusters = []
    
    paginator = rds.get_paginator('describe_db_clusters')
    for page in paginator.paginate():
        clusters.extend(page['DBClusters'])
    
    return clusters

def get_vector_database_info(cluster):
    rds = boto3.client('rds')
    vector_dbs = []
    
    instances = cluster.get('DBClusterMembers', [])
    
    for instance in instances:
        instance_id = instance['DBInstanceIdentifier']
        response = rds.describe_db_instances(DBInstanceIdentifier=instance_id)
        db_instance = response['DBInstances'][0]
        
        if 'vector' in instance_id.lower():
            vector_dbs.append({
                'id': instance_id,
                'size': db_instance['AllocatedStorage'],  # Size in GB
                'engine': db_instance['Engine'],
                'engine_version': db_instance['EngineVersion']
            })
    
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
    clusters = get_aurora_clusters()
    total_vector_dbs = 0
    affected_clusters = 0
    region = boto3.session.Session().region_name
    
    print(f"{YELLOW}Aurora集群向量数据库统计:{ENDC}")
    print("=" * 80)
    
    for cluster in clusters:
        vector_dbs = get_vector_database_info(cluster)
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

if __name__ == "__main__":
    main()