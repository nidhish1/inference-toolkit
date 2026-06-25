# qsentia-model-register

Registers uploaded model bundles into DynamoDB.

Flow:

```text
S3 manifest upload
-> EventBridge rule
-> Lambda
-> DynamoDB qsentia-model-registry
```

Expected trigger key:

```text
models/{model_name}/versions/{model_version}/manifest.json
```

## DynamoDB Item

The Lambda writes:

```json
{
  "model_name": "btc-hybrid-ensemble",
  "model_version": "20260524_125657_utc",
  "env": "staging",
  "status": "inactive",
  "artifact_uri": "s3://bucket/models/btc-hybrid-ensemble/versions/20260524_125657_utc/",
  "endpoint_url": ""
}
```

## Package Lambda

```bash
cd /Users/mudrex/Qsentia/inference-toolkit/lambdas/qsentia-model-register
zip -r function.zip lambda_function.py
```

## Update Lambda Code

```bash
aws lambda update-function-code \
  --function-name qsentia-model-register \
  --zip-file fileb://function.zip
```

## Set Env Vars

```bash
aws lambda update-function-configuration \
  --function-name qsentia-model-register \
  --environment "Variables={MODEL_REGISTRY_TABLE=qsentia-model-registry,DEFAULT_ENV=staging,DEFAULT_STATUS=inactive}"
```

## IAM Permissions

```bash
aws iam put-role-policy \
  --role-name qsentia-model-register-role \
  --policy-name qsentia-model-register-access \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["s3:GetObject"],
        "Resource": "arn:aws:s3:::'"$MODEL_BUCKET"'/models/*"
      },
      {
        "Effect": "Allow",
        "Action": ["dynamodb:PutItem"],
        "Resource": "arn:aws:dynamodb:us-east-2:818680680171:table/qsentia-model-registry"
      }
    ]
  }'
```

## Enable S3 EventBridge

```bash
aws s3api put-bucket-notification-configuration \
  --bucket "$MODEL_BUCKET" \
  --region us-east-2 \
  --notification-configuration '{"EventBridgeConfiguration":{}}'
```

Verify:

```bash
aws s3api get-bucket-notification-configuration \
  --bucket "$MODEL_BUCKET" \
  --region us-east-2
```

Expected:

```json
{
  "EventBridgeConfiguration": {}
}
```

## EventBridge Rule

```bash
aws events put-rule \
  --name qsentia-model-uploaded \
  --region us-east-2 \
  --event-pattern '{
    "source": ["aws.s3"],
    "detail-type": ["Object Created"],
    "detail": {
      "bucket": {
        "name": ["'"$MODEL_BUCKET"'"]
      },
      "object": {
        "key": [{
          "suffix": "manifest.json"
        }]
      }
    }
  }'
```

Attach Lambda:

```bash
export LAMBDA_ARN=$(aws lambda get-function \
  --function-name qsentia-model-register \
  --query Configuration.FunctionArn \
  --output text)

aws events put-targets \
  --rule qsentia-model-uploaded \
  --region us-east-2 \
  --targets "Id"="1","Arn"="$LAMBDA_ARN"
```

Allow EventBridge invoke:

```bash
export RULE_ARN=$(aws events describe-rule \
  --name qsentia-model-uploaded \
  --region us-east-2 \
  --query Arn \
  --output text)

aws lambda add-permission \
  --function-name qsentia-model-register \
  --statement-id qsentia-model-uploaded-eventbridge \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn "$RULE_ARN"
```

If permission already exists, that is fine.

## Test Registration

Create test manifest:

```bash
cat > manifest.json <<'JSON'
{
  "model_name": "btc-hybrid-ensemble",
  "model_version": "test-v1",
  "framework": "ensemble",
  "description": "test registration from s3 event"
}
JSON
```

Upload trigger file:

```bash
aws s3 cp manifest.json \
  "s3://$MODEL_BUCKET/models/btc-hybrid-ensemble/versions/test-v1/manifest.json"
```

Check DynamoDB:

```bash
aws dynamodb get-item \
  --table-name qsentia-model-registry \
  --key '{
    "model_name": {"S": "btc-hybrid-ensemble"},
    "model_version": {"S": "test-v1"}
  }'
```

## Upload Real Model

Upload model files first:

```bash
aws s3 sync \
  best_model_20260524_125657_utc/ \
  "s3://$MODEL_BUCKET/models/btc-hybrid-ensemble/versions/20260524_125657_utc/" \
  --exclude "metadata.json" \
  --exclude "manifest.json"
```

Upload `manifest.json` last:

```bash
aws s3 cp manifest.json \
  "s3://$MODEL_BUCKET/models/btc-hybrid-ensemble/versions/20260524_125657_utc/manifest.json"
```

## Debugging

Check Lambda exists:

```bash
aws lambda get-function \
  --function-name qsentia-model-register \
  --query 'Configuration.[FunctionName,State,Role]'
```

Manually invoke Lambda:

```bash
aws lambda invoke \
  --function-name qsentia-model-register \
  --payload '{}' \
  response.json

cat response.json
```

Check logs:

```bash
aws logs tail /aws/lambda/qsentia-model-register --since 10m
```

Check rule pattern:

```bash
aws events describe-rule \
  --name qsentia-model-uploaded \
  --region us-east-2 \
  --query EventPattern \
  --output json
```

Check rule targets:

```bash
aws events list-targets-by-rule \
  --rule qsentia-model-uploaded \
  --region us-east-2
```

Check EventBridge matched events:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name MatchedEvents \
  --dimensions Name=RuleName,Value=qsentia-model-uploaded \
  --start-time "$(date -u -v-10M +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --period 60 \
  --statistics Sum \
  --region us-east-2
```

Check EventBridge failed invocations:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name FailedInvocations \
  --dimensions Name=RuleName,Value=qsentia-model-uploaded \
  --start-time "$(date -u -v-10M +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --period 60 \
  --statistics Sum \
  --region us-east-2
```

Check S3 EventBridge config:

```bash
aws s3api get-bucket-notification-configuration \
  --bucket "$MODEL_BUCKET" \
  --region us-east-2
```

Check bucket region:

```bash
aws s3api get-bucket-location \
  --bucket "$MODEL_BUCKET"
```

