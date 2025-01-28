# AWS S3 Cost Optimization Calculator

## Table of Contents
- [Storage Cost Calculations](#storage-cost-calculations)
- [Request Cost Calculations](#request-cost-calculations)
- [Lifecycle Cost Calculations](#lifecycle-cost-calculations)
- [ROI Calculations](#roi-calculations)
- [Transfer Cost Calculations](#transfer-cost-calculations)

## Storage Cost Calculations

### Tiered Storage Cost Calculation
```bash
calculate_tiered_storage_cost() {
    local size_gb=$1
    local storage_class=$2
}
```

#### Example Calculation:
For a bucket with 1000 GB in STANDARD storage:

1. First 50 TB tier:
```
1000 GB * $0.023 = $23.00
```

For STANDARD_IA with 1000 GB:
```
1000 GB * $0.0125 = $12.50
```

#### Storage Class Pricing (Seoul Region)
```bash
STORAGE_COSTS=(
    ["STANDARD"]="0.023"        # Per GB/month
    ["STANDARD_IA"]="0.0125"    # Per GB/month
    ["ONEZONE_IA"]="0.01"       # Per GB/month
    ["GLACIER_INSTANT"]="0.004" # Per GB/month
    ["GLACIER_FLEXIBLE"]="0.0036" # Per GB/month
    ["GLACIER_DEEP"]="0.002"    # Per GB/month
)
```

## Request Cost Calculations

### API Request Cost Calculation
```bash
calculate_request_costs() {
    local bucket=$1
    local account_dir=$2
}
```

#### Example Calculation:
For a bucket with:
- 1,000,000 GET requests
- 100,000 PUT requests

```
GET Costs = (1,000,000/1000) * $0.0004 = $0.40
PUT Costs = (100,000/1000) * $0.005 = $0.50
Total Request Cost = $0.90
```

#### Request Pricing
```bash
REQUEST_COSTS=(
    ["GET"]="0.0004"           # Per 1000 requests
    ["PUT"]="0.005"            # Per 1000 requests
    ["LIFECYCLE"]="0.01"       # Per 1000 requests
)
```

## Lifecycle Cost Calculations

### Transition Cost Calculation
```bash
calculate_lifecycle_costs() {
    local size_gb=$1
    local current_class=$2
    local target_class=$3
}
```

#### Example Calculation:
For transitioning 1000 GB from STANDARD to GLACIER_INSTANT:

1. Transition Cost:
```
1000 GB * $0.01 = $10.00 (transition fee)
```

2. Minimum Storage Duration Risk:
```
For GLACIER_INSTANT (90-day minimum):
1000 GB * $0.004 * (90/30) = $12.00 (minimum storage cost risk)
```

#### Minimum Storage Duration Rules:
- STANDARD_IA/ONEZONE_IA: 30 days
- GLACIER_INSTANT/FLEXIBLE: 90 days
- GLACIER_DEEP: 180 days

## ROI Calculations

### Return on Investment Calculation
```bash
calculate_roi() {
    local current_cost=$1
    local target_cost=$2
    local transition_cost=$3
}
```

#### Example Calculation:
For a bucket with:
- Current monthly cost: $100
- Target monthly cost: $40
- Transition cost: $180

```
Monthly Savings = $100 - $40 = $60
Breakeven Months = $180 / $60 = 3 months
```

#### ROI Analysis Includes:
1. Monthly savings calculation
2. Breakeven period
3. First-year savings projection
4. Three-year savings projection

## Transfer Cost Calculations

### Data Transfer Cost Calculation
```bash
calculate_transfer_costs() {
    local size_gb=$1
    local region=$2
}
```

#### Example Calculation:
For transferring 1000 GB out of Seoul region:

```
Transfer Cost = 1000 GB * $0.09 = $90.00
```

#### Transfer Pricing (Seoul Region):
- Data Transfer OUT: $0.09 per GB
- Data Transfer IN: Free

## Real-World Example

Consider a 1000 GB bucket in STANDARD storage with:
- 1M monthly GET requests
- 100K monthly PUT requests
- 50% data accessed infrequently

### Current Costs:
```
Storage: 1000 GB * $0.023 = $23.00
Requests: 
  GET: (1,000,000/1000) * $0.0004 = $0.40
  PUT: (100,000/1000) * $0.005 = $0.50
Total Current Cost = $23.90 per month
```

### Optimization Recommendation:
Move 500 GB to STANDARD_IA:

```
New Storage Cost:
  STANDARD: 500 GB * $0.023 = $11.50
  STANDARD_IA: 500 GB * $0.0125 = $6.25

Transition Cost:
  500 GB * $0.01 = $5.00

Monthly Savings = $23.90 - ($11.50 + $6.25) = $6.15
Breakeven Period = $5.00 / $6.15 = 0.81 months
```

## Monitoring Cost Calculations

### Intelligent-Tiering Monitoring Cost
```bash
calculate_intelligent_tiering_monitoring_cost() {
    local object_count=$1
    echo "scale=4; (${object_count}/1000) * 0.0025" | bc
}
```

#### Example Calculation:
For a bucket with 1,000,000 objects:
```
Monitoring Cost = (1,000,000/1000) * $0.0025 = $2.50 per month
```

This detailed calculation guide helps understand:
- How each cost component is calculated
- The pricing structure for different services
- How optimization recommendations are determined
- The ROI calculation methodology

All calculations use current AWS pricing for the Seoul region (ap-northeast-2) as of January 2024.
