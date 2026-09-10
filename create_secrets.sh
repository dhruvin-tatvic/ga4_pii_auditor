#!/bin/bash
PROJECT="tvc-ga4-pii-auditor"

while IFS='=' read -r key value; do
    if [[ -z "$key" ]] || [[ "$key" == \#* ]]; then
        continue
    fi
    value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//')
    
    echo "Creating secret: $key"
    gcloud secrets create "$key" --replication-policy="automatic" --project="$PROJECT" || echo "Secret $key already exists"
    echo -n "$value" | gcloud secrets versions add "$key" --data-file=- --project="$PROJECT"
done < .env
