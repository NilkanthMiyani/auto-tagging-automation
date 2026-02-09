import json
import boto3

ec2_client = boto3.client('ec2')
s3_client = boto3.client('s3')
rds_client = boto3.client('rds')
lambda_client = boto3.client('lambda')
dynamodb_client = boto3.client('dynamodb')
sns_client = boto3.client('sns')
sqs_client = boto3.client('sqs')
elasticache_client = boto3.client('elasticache')


def lambda_handler(event, context):
    """
    Auto-tags AWS resources based on CloudTrail events.
    Extracts the creator username and applies CreatedBy tag.
    """
    
    try:
        # Parse the event
        detail = event.get('detail', {})
        event_name = detail.get('eventName')
        event_source = detail.get('eventSource')
        user_identity = detail.get('userIdentity', {})
        
        # Extract username
        username = get_username(user_identity)
        
        if not username:
            print("Could not determine username from event")
            return {
                'statusCode': 400,
                'body': json.dumps('Could not determine username')
            }
        
        print(f"Event: {event_name}, Source: {event_source}, User: {username}")
        
        # Tag resources based on event type
        if 'ec2' in event_source.lower():
            tag_ec2_resource(detail, username, event_name)
        elif 's3' in event_source.lower():
            tag_s3_resource(detail, username, event_name)
        elif 'rds' in event_source.lower():
            tag_rds_resource(detail, username, event_name)
        elif 'lambda' in event_source.lower():
            tag_lambda_resource(detail, username, event_name)
        elif 'dynamodb' in event_source.lower():
            tag_dynamodb_resource(detail, username, event_name)
        elif 'sns' in event_source.lower():
            tag_sns_resource(detail, username, event_name)
        elif 'sqs' in event_source.lower():
            tag_sqs_resource(detail, username, event_name)
        elif 'elasticache' in event_source.lower():
            tag_elasticache_resource(detail, username, event_name)
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Successfully tagged resource. Creator: {username}')
        }
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }


def get_username(user_identity):
    """Extract username from CloudTrail user identity."""
    
    # Try principal ID first (contains username for IAM users)
    principal_id = user_identity.get('principalId', '')
    if principal_id and ':' in principal_id:
        # Format is typically "AIDAJ45Q7YFFAREXAMPLE:username"
        username = principal_id.split(':')[-1]
        if username and username != 'ANONYMOUS':
            return username
    
    # Try arn
    arn = user_identity.get('arn', '')
    if arn:
        # Format: arn:aws:iam::123456789012:user/username
        if '/user/' in arn:
            username = arn.split('/user/')[-1]
            return username
        elif ':role/' in arn:
            # For assumed roles
            role_name = arn.split(':role/')[-1]
            # Extract just the role name without session name
            if '/' in role_name:
                role_name = role_name.split('/')[0]
            return role_name
    
    # Try userName field (available for IAM users)
    user_name = user_identity.get('userName')
    if user_name:
        return user_name
    
    # Fallback to accountId if all else fails
    account_id = user_identity.get('accountId', 'unknown')
    return f"aws-account-{account_id}"


def tag_ec2_resource(detail, username, event_name):
    """Tag EC2 resources."""
    try:
        if event_name == 'RunInstances':
            # Extract instance IDs from response elements
            response_elements = detail.get('responseElements', {})
            instances = response_elements.get('instancesSet', {}).get('items', [])
            
            instance_ids = [inst.get('instanceId') for inst in instances if inst.get('instanceId')]
            
            if instance_ids:
                print(f"Tagging EC2 instances: {instance_ids}")
                ec2_client.create_tags(
                    Resources=instance_ids,
                    Tags=[
                        {'Key': 'CreatedBy', 'Value': username}
                    ]
                )
        
        elif event_name == 'CreateVolume':
            response_elements = detail.get('responseElements', {})
            volume_id = response_elements.get('volumeId')
            
            if volume_id:
                print(f"Tagging EBS volume: {volume_id}")
                ec2_client.create_tags(
                    Resources=[volume_id],
                    Tags=[
                        {'Key': 'CreatedBy', 'Value': username}
                    ]
                )
    
    except Exception as e:
        print(f"Error tagging EC2 resource: {str(e)}")
        raise


def tag_s3_resource(detail, username, event_name):
    """Tag S3 resources."""
    try:
        if event_name == 'CreateBucket':
            request_parameters = detail.get('requestParameters', {})
            bucket_name = request_parameters.get('bucketName')
            
            if bucket_name:
                print(f"Tagging S3 bucket: {bucket_name}")
                s3_client.put_bucket_tagging(
                    Bucket=bucket_name,
                    Tagging={
                        'TagSet': [
                            {'Key': 'CreatedBy', 'Value': username}
                        ]
                    }
                )
    
    except Exception as e:
        print(f"Error tagging S3 resource: {str(e)}")
        raise


def tag_rds_resource(detail, username, event_name):
    """Tag RDS resources."""
    try:
        if event_name == 'CreateDBInstance':
            request_parameters = detail.get('requestParameters', {})
            db_instance_id = request_parameters.get('dBInstanceIdentifier')
            
            if db_instance_id:
                # Get the resource ARN
                db_instances = rds_client.describe_db_instances(
                    DBInstanceIdentifier=db_instance_id
                )
                
                if db_instances['DBInstances']:
                    resource_arn = db_instances['DBInstances'][0]['DBInstanceArn']
                    
                    print(f"Tagging RDS instance: {db_instance_id}")
                    rds_client.add_tags_to_resource(
                        ResourceName=resource_arn,
                        Tags=[
                            {'Key': 'CreatedBy', 'Value': username}
                        ]
                    )
    
    except Exception as e:
        print(f"Error tagging RDS resource: {str(e)}")
        raise


def tag_lambda_resource(detail, username, event_name):
    """Tag Lambda resources."""
    try:
        if event_name == 'CreateFunction':
            response_elements = detail.get('responseElements', {})
            function_arn = response_elements.get('functionArn')
            function_name = response_elements.get('functionName')
            
            if function_arn:
                print(f"Tagging Lambda function: {function_name}")
                lambda_client.tag_resource(
                    Resource=function_arn,
                    Tags={
                        'CreatedBy': username
                    }
                )
    
    except Exception as e:
        print(f"Error tagging Lambda resource: {str(e)}")
        raise


def tag_dynamodb_resource(detail, username, event_name):
    """Tag DynamoDB resources."""
    try:
        if event_name == 'CreateTable':
            response_elements = detail.get('responseElements', {})
            table_arn = response_elements.get('tableDescription', {}).get('tableArn')
            table_name = response_elements.get('tableDescription', {}).get('tableName')
            
            if table_arn:
                print(f"Tagging DynamoDB table: {table_name}")
                dynamodb_client.tag_resource(
                    ResourceArn=table_arn,
                    Tags=[
                        {'Key': 'CreatedBy', 'Value': username}
                    ]
                )
    
    except Exception as e:
        print(f"Error tagging DynamoDB resource: {str(e)}")
        raise


def tag_sns_resource(detail, username, event_name):
    """Tag SNS resources."""
    try:
        if event_name == 'CreateTopic':
            response_elements = detail.get('responseElements', {})
            topic_arn = response_elements.get('topicArn')
            
            if topic_arn:
                print(f"Tagging SNS topic: {topic_arn}")
                sns_client.tag_resource(
                    ResourceArn=topic_arn,
                    Tags=[
                        {'Key': 'CreatedBy', 'Value': username}
                    ]
                )
    
    except Exception as e:
        print(f"Error tagging SNS resource: {str(e)}")
        raise


def tag_sqs_resource(detail, username, event_name):
    """Tag SQS resources."""
    try:
        if event_name == 'CreateQueue':
            response_elements = detail.get('responseElements', {})
            queue_url = response_elements.get('queueUrl')
            
            if queue_url:
                print(f"Tagging SQS queue: {queue_url}")
                sqs_client.tag_queue_url(
                    QueueUrl=queue_url,
                    Tags={
                        'CreatedBy': username
                    }
                )
    
    except Exception as e:
        print(f"Error tagging SQS resource: {str(e)}")
        raise


def tag_elasticache_resource(detail, username, event_name):
    """Tag ElastiCache resources."""
    try:
        if event_name == 'CreateCacheCluster':
            response_elements = detail.get('responseElements', {})
            cache_cluster_id = response_elements.get('cacheClusterId')
            
            if cache_cluster_id:
                # Get the replication group ARN
                cache_clusters = elasticache_client.describe_cache_clusters(
                    CacheClusterId=cache_cluster_id
                )
                
                if cache_clusters['CacheClusters']:
                    resource_arn = cache_clusters['CacheClusters'][0]['ARN']
                    
                    print(f"Tagging ElastiCache cluster: {cache_cluster_id}")
                    elasticache_client.add_tags_to_resource(
                        ResourceName=resource_arn,
                        Tags=[
                            {'Key': 'CreatedBy', 'Value': username}
                        ]
                    )
    
    except Exception as e:
        print(f"Error tagging ElastiCache resource: {str(e)}")
        raise
