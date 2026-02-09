# Architecture & How It Works

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Account                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. User Creates Resource                                        │
│     $ aws ec2 run-instances ...                                  │
│                 ↓                                                 │
│  2. API Call Logged by CloudTrail                                │
│     CloudTrail → S3 Bucket (cloudtrail-logs-*.json)             │
│                 ↓                                                 │
│  3. EventBridge Rule Detects Event                               │
│     Rule: auto-tag-create-resources                              │
│     Filter: eventName in [RunInstances, CreateBucket, ...]      │
│                 ↓                                                 │
│  4. Lambda Function Triggered                                    │
│     Function: auto-resource-tagger                               │
│                 ↓                                                 │
│  5. Extract Username from CloudTrail Event                       │
│     userIdentity → principalId → username                        │
│                 ↓                                                 │
│  6. Tag Resource                                                  │
│     ec2:CreateTags {CreatedBy: username}                         │
│                 ↓                                                 │
│  ✅ Resource Tagged Automatically!                              │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. CloudTrail
```
Purpose: Logs all API calls in AWS account
Stores:  S3 bucket (cloudtrail-logs-[AccountID]-[Region])
Format:  JSON logs with full request/response details
Includes: userIdentity, eventName, requestParameters, etc.

Events captured:
  - RunInstances (EC2)
  - CreateBucket (S3)
  - CreateDBInstance (RDS)
  - CreateFunction (Lambda)
  - CreateTable (DynamoDB)
  - CreateTopic (SNS)
  - CreateQueue (SQS)
  - CreateCacheCluster (ElastiCache)
```

### 2. EventBridge Rule
```
Purpose: Matches events and routes them to targets
Rule: auto-tag-create-resources
Status: ENABLED

Event Pattern Matches:
{
  "source": ["aws.ec2", "aws.s3", "aws.rds", "aws.lambda", ...],
  "detail-type": ["AWS API Call via CloudTrail"],
  "detail": {
    "eventName": ["RunInstances", "CreateBucket", ...]
  }
}

Target: Lambda function (auto-resource-tagger)
Invocation: Synchronous (waits for Lambda to complete)
```

### 3. Lambda Function
```
Name: auto-resource-tagger
Runtime: Python 3.13
Memory: 256 MB
Timeout: 30 seconds

Logic:
  1. Receive event from EventBridge
  2. Extract: eventName, eventSource, userIdentity
  3. Get username from userIdentity (multiple sources)
  4. Route to appropriate handler (EC2, S3, RDS, etc.)
  5. Apply tags using AWS APIs
  6. Return success/error

Permissions Needed:
  - ec2:CreateTags
  - s3:PutBucketTagging
  - rds:AddTagsToResource
  - lambda:TagResource
  - dynamodb:TagResource
  - sns:TagResource
  - sqs:TagQueueUrl
  - elasticache:AddTagsToResource
```

### 4. IAM Role
```
Role: AutoResourceTaggerRole
Trust: Lambda service (lambda.amazonaws.com)

Inline Policy: AutoResourceTaggerPolicy
Permissions:
  - Tag all resources (ec2:CreateTags, s3:PutBucketTagging, etc.)
  - Describe resources (needed for ARN lookup)
  - CloudWatch Logs (for Lambda logs)
```

## Data Flow Example

### Scenario: EC2 Instance Creation

```
Step 1: User Creates Instance
───────────────────────────────
$ aws ec2 run-instances --image-id ami-xxx --instance-type t2.micro
{
  "Instances": [{
    "InstanceId": "i-0123456789abcdef",
    "State": "pending"
  }]
}
⏱️ Time: T+0 seconds

Step 2: CloudTrail Logs the Call
────────────────────────────────
CloudTrail Event:
{
  "eventName": "RunInstances",
  "eventSource": "ec2.amazonaws.com",
  "userIdentity": {
    "principalId": "AIDAI12345:nilkanth",
    "userName": "nilkanth",
    "arn": "arn:aws:iam::992382787256:user/nilkanth"
  },
  "responseElements": {
    "instancesSet": {
      "items": [{
        "instanceId": "i-0123456789abcdef"
      }]
    }
  }
}
⏱️ Time: T+1 second (CloudTrail latency)

Step 3: EventBridge Detects Event
──────────────────────────────────
Rule matches:
  ✓ source = "aws.ec2"
  ✓ detail-type = "AWS API Call via CloudTrail"
  ✓ eventName = "RunInstances"

EventBridge invokes Lambda with the full CloudTrail event
⏱️ Time: T+1.2 seconds

Step 4: Lambda Extracts Username
─────────────────────────────────
def get_username(user_identity):
    principal_id = "AIDAI12345:nilkanth"
    username = principal_id.split(':')[-1]
    return "nilkanth"  # ← Username extracted!
⏱️ Time: T+1.3 seconds

Step 5: Lambda Tags EC2 Instance
─────────────────────────────────
ec2_client.create_tags(
    Resources=["i-0123456789abcdef"],
    Tags=[{'Key': 'CreatedBy', 'Value': 'nilkanth'}]
)

EC2 API call succeeds
⏱️ Time: T+1.5 seconds

Step 6: User Checks Tags
────────────────────────
$ aws ec2 describe-instances --instance-ids i-0123456789abcdef

Response:
{
  "Tags": [
    {
      "Key": "CreatedBy",
      "Value": "nilkanth"  # ← Tag appears!
    }
  ]
}
⏱️ Time: T+2 seconds
```

## Username Extraction Priority

Lambda tries multiple methods to extract username:

```
1. principalId field
   "AIDAI12345:nilkanth" → Extract "nilkanth" ✅

2. arn field with /user/
   "arn:aws:iam::992382787256:user/nilkanth" → "nilkanth" ✅

3. arn field with :role/
   "arn:aws:iam::992382787256:role/my-role/session" → "my-role" ✅

4. userName field
   "nilkanth" → "nilkanth" ✅

5. Fallback
   Use accountId: "aws-account-992382787256" ⚠️
```

## Latency Breakdown

```
CloudTrail Write:     100ms    (API call logged)
CloudTrail→S3:        500ms    (batch write to S3)
EventBridge Match:    200ms    (rule evaluation)
Lambda Invoke:        100ms    (cold start first time, <10ms warm)
Lambda Execution:     300ms    (tag API calls)
─────────────────────────────
Total E2E:          1-2 seconds
```

## Multi-Account Architecture

For organizations with multiple AWS accounts:

```
AWS Organization
  ├─ Management Account (monitoring)
  ├─ Development Account
  │   └─ CloudFormation Stack
  │       └─ CloudTrail, Lambda, EventBridge
  ├─ Staging Account
  │   └─ CloudFormation Stack
  │       └─ CloudTrail, Lambda, EventBridge
  └─ Production Account
      └─ CloudFormation Stack
          └─ CloudTrail, Lambda, EventBridge

Each account has:
  - Independent CloudTrail trail
  - Independent Lambda function
  - Independent EventBridge rule
  - No cross-account dependencies
  - Isolated tagging per account
```

## Scaling Considerations

### Performance
- Lambda: Handles 1000s of concurrent invocations
- EventBridge: Processes millions of events per second
- Tagging APIs: Highly scalable (AWS backend)
- **No bottlenecks** up to 1 million resources/month

### Cost Scaling
```
Monthly Resources | Cost/Month | Cost Driver
──────────────────────────────────────────
500               | $0.01      | S3 storage
5,000             | $0.05      | S3 storage
50,000            | $0.50      | S3 storage
500,000           | $11        | CloudTrail (after free tier)
5,000,000         | $110       | CloudTrail
```

### Tagging Latency
```
Volume         | Latency    | Notes
──────────────────────────────────
100/min        | <1s        | Instant
1,000/min      | 1-2s       | Warm Lambda
10,000/min     | 2-5s       | Lambda scaling
100,000/min    | >5s        | May need concurrency increase
```

## Reliability & Failover

### High Availability
- ✅ CloudTrail: Auto-replicated, durable
- ✅ Lambda: Auto-scaling, regional redundancy
- ✅ EventBridge: Managed service, no SLA issues
- ✅ S3: 99.99% uptime SLA

### Error Handling
```python
if not username:
    return error "Could not determine username"
    # Event logged but resource not tagged
    # (resource still created, just untagged)

if tag_fails:
    Lambda execution fails
    EventBridge retries (2 attempts default)
    Resource created but untagged
    # Manual tagging needed
```

### Monitoring
- Lambda errors → CloudWatch Logs
- Failed tagging → Lambda logs (timestamp, error)
- EventBridge failures → CloudWatch Metrics
- User can subscribe to SNS/SQS for alerts

## Cost Optimization

### S3 Lifecycle Policy
```
CloudTrail logs deleted after:
  - 90 days (current version)
  - 30 days (previous versions)
  
Prevents S3 storage costs from growing
```

### Lambda Optimization
```
Memory: 256 MB (optimal for this use case)
Timeout: 30 seconds (more than enough)
Usually completes in <500ms
```

---

**Questions?** Check [README.md](README.md) or [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
