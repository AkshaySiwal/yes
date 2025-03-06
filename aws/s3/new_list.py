import boto3
import csv
import os
from datetime import datetime

def read_data(slave_session):
    s3_client = slave_session.client('s3')
    account_id = slave_session.client('sts').get_caller_identity()['Account']

    buckets_data = []

    # Get list of all buckets
    response = s3_client.list_buckets()

    for bucket in response['Buckets']:
        bucket_name = bucket['Name']

        # Get bucket ARN
        bucket_arn = f"arn:aws:s3:::{bucket_name}"

        # Get bucket tags
        try:
            tags_response = s3_client.get_bucket_tagging(Bucket=bucket_name)
            tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagSet', [])}
        except s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchTagSet':
                tags = 'Not_Found'
            else:
                print(f"Error getting tags for bucket {bucket_name}: {str(e)}")
                tags = e.response['Error']['Code']

        # Determine if created by Terraform
        created_by_terraform = "No"
        role = 'Not_Found'
        if isinstance(tags, dict):
            if (tags.get('Managed_By', '').lower() == 'terraform' or
                tags.get('Created_By', '').lower() == 'terraform' or
                tags.get('Terraform', '').lower() == 'true' or
                (tags.get('tfe_workspace_name', '') != '') or
                tags.get('boltx_terraform', '').lower() == 'true'):
                created_by_terraform = "Yes"
            elif tags.get('terraform.io', '').lower() == 'managed':
                created_by_terraform = "Maybe"

            # Get bucket policy to determine role
            role = tags.get('role', 'Not_Found')
        
            
        

        # Get lifecycle rules
        try:
            lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
            num_lifecycle_rules = len(lifecycle.get('Rules', []))
        except s3_client.exceptions.ClientError:
            # Bucket might not have lifecycle rules
            num_lifecycle_rules = 0

        # Append data
        buckets_data.append({
            'Account ID': account_id,
            'Bucket Name': bucket_name,
            'Bucket ARN': bucket_arn,
            'Created By Terraform': created_by_terraform,
            'Role': role,
            'Number of Lifecycle Rules': num_lifecycle_rules
        })

    return buckets_data

def collect_all_accounts_data(slave_account_ids):
    """
    Collects S3 bucket data from multiple AWS accounts and saves to CSV.

    Args:
        slave_account_ids: List of slave account IDs to process

    Returns:
        str: Path to the generated CSV file
    """
    all_data = []

    for slave_account_id in slave_account_ids:
        try:
            # Assume you have a function to create a session for each account
            # This is a placeholder - you'll need to implement the actual session creation
            slave_session = create_session_for_account(slave_account_id)

            # Get data for this account
            account_data = read_data(slave_session)
            if account_data:  # Only append if there's data to add
                all_data.append(account_data)  # Append individual account data to the list
               

            print(f"Successfully processed account {slave_account_id}")
        except Exception as e:
            print(f"Error processing account {slave_account_id}: {str(e)}")

    # Write all data to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"s3_buckets_inventory_{timestamp}.csv"

    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['Account ID', 'Bucket Name', 'Bucket ARN', 'Created By Terraform', 'Role', 'Number of Lifecycle Rules']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in all_data:
            writer.writerow(row)

    print(f"Data written to {csv_filename}")
    return csv_filename

def create_session_for_account(account_id):
    """
    Creates a boto3 session for the specified AWS account.

    Args:
        account_id: The AWS account ID to create a session for

    Returns:
        boto3.Session: A session for the specified account
    """
    # This is a placeholder implementation
    # In a real scenario, you would use role assumption or other methods
    # to get credentials for the slave account

    # Example using role assumption:
    sts_client = boto3.client('sts')
    role_arn = f"arn:aws:iam::{account_id}:role/CrossAccountAccessRole"

    assumed_role = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName=f"S3BucketInventory-{account_id}"
    )

    credentials = assumed_role['Credentials']

    session = boto3.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )

    return session

# Example usage
if __name__ == "__main__":
    # Example list of slave account IDs
    slave_account_ids = ['123456789012', '234567890123', '345678901234']

    # Collect data from all accounts
    csv_file = collect_all_accounts_data(slave_account_ids)

    # Created/Modified files during execution:
    print(f"Created file: {csv_file}")
