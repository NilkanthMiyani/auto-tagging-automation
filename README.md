# AWS Auto-Tagging Automation

Automatically tags AWS resources with `CreatedBy` metadata when they're created. Never wonder "who created this?" again.

## Features

- **Automatic**: Tags resources instantly when created (1-5 second latency)
- **No Code Changes**: Uses EventBridge + Lambda, no SDK integration needed
- **Wide Coverage**: Supports 8+ AWS services (EC2, S3, RDS, Lambda, DynamoDB, SNS, SQS, ElastiCache)
- **Low Cost**: ~$25-50/month (mostly CloudTrail storage)
- **Easy to Deploy**: Single CloudFormation command

## Quick Start

1. **Deploy the stack**:
```powershell
aws cloudformation create-stack `
  --stack-name auto-tagging-automation `
  --template-body file://auto-tagging-template.yaml `
  --capabilities CAPABILITY_NAMED_IAM `
  --region us-east-1
```

2. **Wait for completion** (~3-5 minutes)

3. **Create a resource** and it gets tagged automatically with `CreatedBy: your-username`

## What Gets Tagged

| Service | Resources |
|---------|-----------|
| EC2 | Instances, Volumes, Security Groups, VPCs, Subnets |
| S3 | Buckets |
| RDS | Database Instances |
| Lambda | Functions |
| DynamoDB | Tables |
| SNS | Topics |
| SQS | Queues |
| ElastiCache | Clusters |

## How It Works

1. **You create a resource** → AWS API call
2. **CloudTrail logs the call** → S3
3. **EventBridge detects the event** → Triggers Lambda
4. **Lambda extracts the creator** → Reads CloudTrail event
5. **Lambda applies the tag** → `CreatedBy: creator-name`

## Files

- `auto-tagging-template.yaml` - CloudFormation template (deploy this)
- `event-pattern.json` - EventBridge event pattern configuration
- `auto_resource_tagger.py` - Lambda function source code
- `DEPLOYMENT_GUIDE.md` - Detailed deployment instructions
- `ARCHITECTURE.md` - How the system works

## Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Step-by-step deployment, verification, troubleshooting
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical deep-dive, system design, data flow

## Cost

| Component | Cost |
|-----------|------|
| CloudTrail | $25-50/month |
| Lambda | FREE (<1M invocations) |
| EventBridge | FREE (<100K events) |
| S3 | <$1/month (log storage) |
| **Total** | **~$25-100/month** |

## Requirements

- AWS Account with appropriate permissions
- AWS CLI configured
- PowerShell (or adjust commands for your shell)

## Support

Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for troubleshooting and customization options.

## License

MIT
