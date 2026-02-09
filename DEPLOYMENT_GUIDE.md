# Auto-Tagging Automation - CloudFormation Deployment Guide

## Quick Deploy

```powershell
# Deploy the stack
aws cloudformation create-stack `
  --stack-name auto-tagging-automation `
  --template-body file://auto-tagging-template.yaml `
  --capabilities CAPABILITY_NAMED_IAM `
  --region us-east-1

# Check stack status
aws cloudformation describe-stacks `
  --stack-name auto-tagging-automation `
  --query 'Stacks[0].StackStatus' `
  --region us-east-1

# Get outputs (after stack is CREATE_COMPLETE)
aws cloudformation describe-stacks `
  --stack-name auto-tagging-automation `
  --query 'Stacks[0].Outputs' `
  --region us-east-1
```

## What Gets Created

### Infrastructure Components:
1. **CloudTrail Trail** - Logs all API calls to resources
2. **S3 Bucket** - Stores CloudTrail logs (auto-expires after 90 days)
3. **EventBridge Rule** - Detects resource creation events
4. **Lambda Function** - Auto-tags resources with CreatedBy
5. **IAM Role** - Grants Lambda permissions to tag resources
6. **Lambda Permission** - Allows EventBridge to invoke Lambda

## Supported Resources

Automatically tags on creation:
- EC2 Instances & EBS Volumes
- S3 Buckets
- RDS Databases
- Lambda Functions
- DynamoDB Tables
- SNS Topics
- SQS Queues
- ElastiCache Clusters
- VPCs, Subnets, Security Groups

## Verify Deployment

```powershell
# Test with a new Lambda function
aws lambda create-function `
  --function-name test-tagging `
  --runtime python3.13 `
  --role arn:aws:iam::YOUR_ACCOUNT:role/service-role/test-role `
  --handler index.handler `
  --code ZipFile=b'def handler(event, context): return "test"'

# Wait 2-5 seconds, then check tags
aws cloudtrail lookup-events `
  --lookup-attributes AttributeKey=EventName,AttributeValue=CreateFunction `
  --max-results 1
```

## Update Stack

```powershell
# Update existing stack
aws cloudformation update-stack `
  --stack-name auto-tagging-automation `
  --template-body file://auto-tagging-template.yaml `
  --capabilities CAPABILITY_NAMED_IAM `
  --region us-east-1
```

## Delete Stack (if needed)

```powershell
# Warning: This will delete all resources including S3 bucket
aws cloudformation delete-stack `
  --stack-name auto-tagging-automation `
  --region us-east-1
```

## Customization

Edit the template directly to change Lambda timeout or memory:

```yaml
Timeout: 30        # Change timeout here (seconds)
MemorySize: 256    # Change memory here (MB)
```

## Cost Estimation

- **CloudTrail**: $25-50/month (storage)
- **Lambda**: FREE (<1M invocations)
- **EventBridge**: FREE (<100K events)
- **S3**: <$1/month (log storage)
- **Total**: ~$25-100/month for most organizations

## Monitoring

```powershell
# View Lambda logs
aws logs tail /aws/lambda/auto-resource-tagger --follow

# View CloudTrail events
aws cloudtrail lookup-events --max-results 10

# Check EventBridge rule metrics
aws cloudwatch get-metric-statistics `
  --namespace AWS/Events `
  --metric-name Invocations `
  --dimensions Name=RuleName,Value=auto-tag-create-resources `
  --start-time 2026-02-09T00:00:00Z `
  --end-time 2026-02-10T00:00:00Z `
  --period 3600 `
  --statistics Sum
```

## Troubleshooting

**Lambda not being invoked:**
- Check CloudTrail is logging (trail status)
- Verify EventBridge rule is ENABLED
- Check Lambda CloudWatch logs

**Tags not being applied:**
- Check Lambda execution role has correct permissions
- Verify resource creation event matches event pattern
- Check Lambda function logs for errors

**S3 bucket access denied:**
- Ensure bucket policy allows CloudTrail access
- Verify bucket name doesn't have special characters
- Check region matches (must be same for CloudTrail)
