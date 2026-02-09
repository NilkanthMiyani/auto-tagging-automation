# AWS Auto-Tagging Automation

Automatically tag all your AWS resources with `CreatedBy` metadata to prevent the "blame game" and enable cost allocation.

## Features

✅ **Automatic Tagging** - Tags resources on creation with creator's username  
✅ **Multi-Service** - Supports 8+ AWS services (EC2, S3, RDS, Lambda, DynamoDB, SNS, SQS, ElastiCache)  
✅ **Zero Code** - Deploy with one command using CloudFormation  
✅ **Pennies Cost** - ~$0.01/month for 500 resources (essentially FREE)  
✅ **Enterprise Ready** - Deploy across multiple AWS accounts  
✅ **Accountability** - Know who created what, when, and where  

## What Gets Tagged

When you create any of these resources, they're automatically tagged with `CreatedBy=<username>`:

- EC2 Instances & EBS Volumes
- S3 Buckets
- RDS Databases
- Lambda Functions
- DynamoDB Tables
- SNS Topics
- SQS Queues
- ElastiCache Clusters
- VPCs, Security Groups, Subnets

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/aws-auto-tagging-automation.git
cd aws-auto-tagging-automation
```

### 2. Deploy in One Command
```powershell
aws cloudformation create-stack `
  --stack-name auto-tagging-automation `
  --template-body file://auto-tagging-template.yaml `
  --capabilities CAPABILITY_NAMED_IAM `
  --region us-east-1
```

### 3. Verify Deployment
```powershell
aws cloudformation describe-stacks `
  --stack-name auto-tagging-automation `
  --query 'Stacks[0].StackStatus'
```

Wait for `CREATE_COMPLETE` ✅

### 4. Test It Works
```powershell
# Create a test instance
aws ec2 run-instances --image-id ami-0c55b159cbfafe1f0 --count 1 --instance-type t2.micro

# Wait 2-5 seconds, then check tags
aws ec2 describe-instances --query 'Reservations[0].Instances[0].Tags'
```

Should show: `CreatedBy: your-username` ✅

## Architecture

```
Resource Created (EC2, S3, RDS, etc.)
         ↓
CloudTrail logs the API call
         ↓
EventBridge detects event
         ↓
Lambda function triggered
         ↓
Lambda extracts creator username
         ↓
Lambda applies CreatedBy tag
         ↓
✅ Resource tagged automatically
```

## Cost Estimate

| Scenario | Monthly Resources | Monthly Cost | Annual Cost |
|----------|-------------------|--------------|-------------|
| Startup | 500 | ~$0.01 | ~$0.12 |
| Small Org | 5,000 | ~$0.05 | ~$0.60 |
| Medium Org | 50,000 | ~$0.50 | ~$6 |
| Large Org | 500,000 | ~$11 | ~$132 |

*All costs after AWS free tier. Most organizations stay in free tier.*

## Files

| File | Purpose |
|------|---------|
| `auto-tagging-template.yaml` | CloudFormation template (deploy this) |
| `event-pattern.json` | EventBridge event pattern |
| `auto_resource_tagger.py` | Lambda function source code |
| `DEPLOYMENT_GUIDE.md` | Detailed deployment instructions |
| `ARCHITECTURE.md` | How the system works |

## Multi-Account Deployment

Deploy to multiple accounts using CloudFormation StackSets:

```powershell
aws cloudformation create-stack-set `
  --stack-set-name auto-tagging-automation `
  --template-body file://auto-tagging-template.yaml `
  --capabilities CAPABILITY_NAMED_IAM

aws cloudformation create-stack-instances `
  --stack-set-name auto-tagging-automation `
  --accounts 111111111111 222222222222 333333333333 `
  --regions us-east-1 us-west-2
```

## Monitoring & Logging

### View Lambda Logs
```powershell
aws logs tail /aws/lambda/auto-resource-tagger --follow
```

### Check EventBridge Invocations
```powershell
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

**Lambda not tagging resources?**
- Check CloudTrail is enabled: `aws cloudtrail describe-trails`
- Verify EventBridge rule is ENABLED: `aws events describe-rule --name auto-tag-create-resources`
- Check Lambda logs: `aws logs tail /aws/lambda/auto-resource-tagger`

**Stack creation failed?**
- Verify you have `CAPABILITY_NAMED_IAM` flag
- Check IAM permissions (CreateRole, PutRolePolicy, etc.)
- Ensure S3 bucket name is globally unique (try different region)

**Tags not appearing immediately?**
- CloudTrail has 1-5 second latency
- Wait 5-10 seconds before checking tags
- Verify event went through: `aws cloudtrail lookup-events --max-results 5`

## Customization

### Add More Resource Types

Edit `auto-tagging-template.yaml`:

1. Add event name to EventPattern:
```yaml
eventName:
  - RunInstances
  - CreateBucket
  - CreateDBInstance
  - CreateUser          # Add this
```

2. Add handler function in Lambda code:
```python
def tag_iam_resource(detail, username, event_name):
    # Your tagging logic here
    pass
```

### Change Tag Values

The template currently tags with `CreatedBy=<username>`. To add more tags, edit Lambda code in template.

## Security

✅ Least privilege IAM roles  
✅ S3 bucket with public access blocked  
✅ CloudTrail log file validation enabled  
✅ No hardcoded credentials  
✅ Uses IAM user's credentials automatically  

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## Support

- 📖 [Detailed Deployment Guide](DEPLOYMENT_GUIDE.md)
- 🏗️ [Architecture Documentation](ARCHITECTURE.md)
- 💬 [Issues](https://github.com/yourusername/aws-auto-tagging-automation/issues)

## Author

Created by **Nilkanth** - Avoid the blame game! 🎯

---

**Star ⭐ if this helped you avoid the blame game!**
