import boto3
import json
import os
import sys
from datetime import datetime
import csv
from pathlib import Path
from typing import Dict, List, Any


# Get BUILD_NUMBER from environment variable with a fallback
BUILD_NUMBER = os.getenv('BUILD_NUMBER', 'manual')
SESSION_NAME = f"S3Analysis-{BUILD_NUMBER}"


class S3Analyzer:
    def __init__(self, session_name: str, slave_role:str):
        self.session_name = session_name
        self.slave_role = slave_role
        # Use EC2's instance profile for master account
        self.master_session = boto3.Session()
        # self.results = {}

    def assume_slave_role(self, account_id: str, role_name: str) -> boto3.Session:
        try:
            sts_client = self.master_session.client('sts')
            role_arn = f'arn:aws:iam::{account_id}:role/{role_name}'

            response = sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName=self.session_name
            )

            # Create session with temporary credentials
            slave_session = boto3.Session(
                aws_access_key_id=response['Credentials']['AccessKeyId'],
                aws_secret_access_key=response['Credentials']['SecretAccessKey'],
                aws_session_token=response['Credentials']['SessionToken']
            )

            return slave_session

        except Exception as e:
            print(f"Error assuming role in account {account_id}: {str(e)}")
            raise

    def analyze_bucket(self, session: boto3.Session, bucket_name: str, owner_info: Dict = None) -> Dict[str, Any]:
        try:
            s3_client = session.client('s3')

            # Initialize metrics
            metrics = {
                'bucket_name': bucket_name,
                'total_size': 0,
                'total_objects': 0,
                'storage_classes': {},
                'tags': {
                    'has_tags': False,
                    'has_pii': False,
                    'tag_list': []
                },
                'bucket_info': {
                    'region': 'unknown',
                    'owner': owner_info or {'display_name': 'unknown', 'id': 'unknown'},
                    'creation_date': None
                }
            }

            # Get bucket region
            try:
                location = s3_client.get_bucket_location(Bucket=bucket_name)
                metrics['bucket_info']['region'] = location.get('LocationConstraint') or 'us-east-1'
            except Exception as e:
                print(f"Error getting bucket location for {bucket_name}: {str(e)}")

            
            # Check bucket tags first
            try:
                tag_response = s3_client.get_bucket_tagging(Bucket=bucket_name)
                tag_set = tag_response.get('TagSet', [])
                metrics['tags']['has_tags'] = True
                metrics['tags']['tag_list'] = tag_set

                # Check for 'pii' in tags
                for tag in tag_set:
                    if ('pii' in tag['Key'].lower() or
                        'pii' in tag['Value'].lower()):
                        metrics['tags']['has_pii'] = True
                        break

            except s3_client.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchTagSet':
                    metrics['tags']['has_tags'] = False
                else:
                    raise

            # Only analyze bucket contents if it has no tags or has PII tags
            if not metrics['tags']['has_tags'] or metrics['tags']['has_pii']:
                print(f"Analyzing contents of bucket {bucket_name} - No tags: {not metrics['tags']['has_tags']}, Has PII: {metrics['tags']['has_pii']}")

                paginator = s3_client.get_paginator('list_objects_v2')

                for page in paginator.paginate(Bucket=bucket_name):
                    if 'Contents' not in page:
                        continue

                    for obj in page['Contents']:
                        size = obj['Size']
                        storage_class = obj['StorageClass']

                        # Update total metrics
                        metrics['total_size'] += size
                        metrics['total_objects'] += 1

                        # Update storage class metrics
                        if storage_class not in metrics['storage_classes']:
                            metrics['storage_classes'][storage_class] = {
                                'object_count': 0,
                                'total_size': 0
                            }

                        metrics['storage_classes'][storage_class]['object_count'] += 1
                        metrics['storage_classes'][storage_class]['total_size'] += size
            else:
                print(f"Skipping content analysis for bucket {bucket_name} - Has tags but no PII")
                metrics['skipped_analysis'] = True

            return metrics

        except Exception as e:
            print(f"Error analyzing bucket {bucket_name}: {str(e)}")
            return None
    

    def analyze_accounts(self, slave_accounts: List[str], check_master_too: bool = False) -> Dict[str, Any]:
        try:
            results = {'master_account': {}, 'slave_accounts': {}}

            if check_master_too:
                s3_client = self.master_session.client('s3')
                try:
                    # Single list_buckets call for master account
                    list_buckets_response = s3_client.list_buckets()
                    buckets = list_buckets_response['Buckets']
                    owner_info = list_buckets_response['Owner']

                    if len(buckets) >= 1000:
                        print("Warning: Possible bucket list truncation in master account")

                    print("Analyzing master account buckets...")
                    for bucket in buckets:
                        bucket_name = bucket['Name']
                        bucket_result = self.analyze_bucket(self.master_session, bucket_name, owner_info)
                        if bucket_result is not None:
                            bucket_result['bucket_info']['creation_date'] = bucket['CreationDate'].isoformat()
                            results['master_account'][bucket_name] = bucket_result
                        else:
                            print(f"Skipping bucket {bucket_name} due to analysis failure")
                except Exception as e:
                    print(f"Error analyzing master account: {str(e)}")

            for account_id in slave_accounts:
                try:
                    print(f"Analyzing account {account_id}...")
                    slave_session = self.assume_slave_role(account_id, self.slave_role)
                    s3_client = slave_session.client('s3')

                    # Single list_buckets call for each slave account
                    list_buckets_response = s3_client.list_buckets()
                    buckets = list_buckets_response['Buckets']
                    owner_info = list_buckets_response['Owner']

                    if len(buckets) >= 1000:
                        print(f"Warning: Possible bucket list truncation in account {account_id}")

                    results['slave_accounts'][account_id] = {}
                    for bucket in buckets:
                        bucket_name = bucket['Name']
                        bucket_result = self.analyze_bucket(slave_session, bucket_name, owner_info)
                        if bucket_result is not None:
                            bucket_result['bucket_info']['creation_date'] = bucket['CreationDate'].isoformat()
                            results['slave_accounts'][account_id][bucket_name] = bucket_result
                        else:
                            print(f"Skipping bucket {bucket_name} in account {account_id} due to analysis failure")
                except Exception as e:
                    print(f"Error analyzing account {account_id}: {str(e)}")
                    continue

            return results
        except Exception as e:
            print(f"Fatal error in account analysis: {str(e)}")
            raise

    

class Utility:
    @staticmethod
    def format_bytes(bytes_size: int) -> str:
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} TB"
    @staticmethod
    def print_account_summary(account_name: str, buckets_data: Dict[str, Any]) -> None:
        print(f"\n{account_name}:")

        # Track buckets with no tags and PII tags
        untagged_buckets = []
        pii_buckets = []
        analyzed_buckets = []

        for bucket_name, metrics in buckets_data.items():
            # Track buckets based on tags
            if not metrics['tags']['has_tags']:
                untagged_buckets.append(bucket_name)
            if metrics['tags']['has_pii']:
                pii_buckets.append(bucket_name)
            if not metrics.get('skipped_analysis'):
                analyzed_buckets.append(bucket_name)

            print(f"\nBucket: {bucket_name}")
            print(f"Region: {metrics['bucket_info']['region']}")
            print(f"Owner: {metrics['bucket_info']['owner']['display_name']} ({metrics['bucket_info']['owner']['id']})")
            print(f"Created: {metrics['bucket_info']['creation_date']}")
            print(f"Tags: {'Yes' if metrics['tags']['has_tags'] else 'No'}")
            print(f"Contains PII Tag: {'Yes' if metrics['tags']['has_pii'] else 'No'}")
            

            if not metrics.get('skipped_analysis'):
                print(f"Total Size: {Utility.format_bytes(metrics['total_size'])}")
                print(f"Total Objects: {metrics['total_objects']}")
                print("Storage Classes:")
                for storage_class, stats in metrics['storage_classes'].items():
                    print(f"  {storage_class}:")
                    print(f"    Objects: {stats['object_count']}")
                    print(f"    Size: {Utility.format_bytes(stats['total_size'])}")
            else:
                print("Content analysis skipped - Has tags but no PII")

        # Print tag summary
        print(f"\nUntagged Buckets ({len(untagged_buckets)}):")
        for bucket in untagged_buckets:
            print(f"  - {bucket}")

        print(f"\nBuckets with PII Tags ({len(pii_buckets)}):")
        for bucket in pii_buckets:
            print(f"  - {bucket}")

        print(f"\nBuckets Analyzed ({len(analyzed_buckets)}):")
        for bucket in analyzed_buckets:
            print(f"  - {bucket}")

    
    @staticmethod
    def save_to_csv(account_id: str, buckets_data: Dict[str, Any], output_dir: Path):
        csv_filename = output_dir / f"s3_analysis_{account_id}.csv"

        # First pass: collect all unique storage classes across all buckets
        storage_classes = set()
        for metrics in buckets_data.values():
            if not metrics.get('skipped_analysis'):
                storage_classes.update(metrics['storage_classes'].keys())

        # Sort storage classes for consistent column ordering
        storage_classes = sorted(list(storage_classes))

        # Define CSV headers
        base_headers = [
            'Bucket Name',
            'Region',
            'Owner Display Name',
            'Owner ID',
            'Creation Date',
            'Has Tags',
            'Has PII Tags',
            'Total Size (Bytes)',
            'Total Size (Human Readable)',
            'Total Objects'
        ]

        # Add columns for each storage class (size and count)
        storage_class_headers = []
        for sc in storage_classes:
            storage_class_headers.extend([
                f'{sc}_Objects',
                f'{sc}_Size'
            ])

        headers = base_headers + storage_class_headers + ['Tag List']

        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()

            for bucket_name, metrics in buckets_data.items():
                # Prepare tag list string
                tag_list = [f"{tag['Key']}={tag['Value']}"
                        for tag in metrics['tags'].get('tag_list', [])]

                # Initialize row with base data
                row = {
                    'Bucket Name': bucket_name,
                    'Region': metrics['bucket_info']['region'],
                    'Owner Display Name': metrics['bucket_info']['owner']['display_name'],
                    'Owner ID': metrics['bucket_info']['owner']['id'],
                    'Creation Date': metrics['bucket_info']['creation_date'],
                    'Has Tags': 'Yes' if metrics['tags']['has_tags'] else 'No',
                    'Has PII Tags': 'Yes' if metrics['tags']['has_pii'] else 'No',
                    'Total Size (Bytes)': metrics['total_size'] if not metrics.get('skipped_analysis') else 'Not Analyzed',
                    'Total Size (Human Readable)': Utility.format_bytes(metrics['total_size']) if not metrics.get('skipped_analysis') else 'Not Analyzed',
                    'Total Objects': metrics['total_objects'] if not metrics.get('skipped_analysis') else 'Not Analyzed',
                    'Tag List': '; '.join(tag_list) if tag_list else 'No Tags'
                }

                # Add storage class data
                if not metrics.get('skipped_analysis'):
                    for sc in storage_classes:
                        if sc in metrics['storage_classes']:
                            row[f'{sc}_Objects'] = metrics['storage_classes'][sc]['object_count']
                            row[f'{sc}_Size'] = metrics['storage_classes'][sc]['total_size']
                        else:
                            row[f'{sc}_Objects'] = 0
                            row[f'{sc}_Size'] = 0
                else:
                    for sc in storage_classes:
                        row[f'{sc}_Objects'] = 'Not Analyzed'
                        row[f'{sc}_Size'] = 'Not Analyzed'

                writer.writerow(row)

        print(f"CSV report saved as: {csv_filename}")







if __name__ == "__main__":
    # Configuration


    # List of slave accounts to analyze
    SLAVE_ACCOUNTS = [ '111111111111' ]
    SLAVE_ROLE = 'xyx'
    CHECK_MASTER = True


    # Validate configuration
    if not SLAVE_ACCOUNTS:
        print("Error: No slave accounts provided")
        sys.exit(1)

    if not SLAVE_ROLE:
        print("Error: No slave role provided")
        sys.exit(1)


    # Initialize and run analysis
    analyzer = S3Analyzer(session_name=SESSION_NAME, slave_role=SLAVE_ROLE)
    results = analyzer.analyze_accounts(slave_accounts=SLAVE_ACCOUNTS, check_master_too=CHECK_MASTER)

    
    # Create output directory for reports
    try:
        output_dir = Path(f"s3_analysis_reports_{BUILD_NUMBER}")
        output_dir.mkdir(exist_ok=True)
    except PermissionError:
        print("Error: Permission denied when creating output directory")
        sys.exit(1)
    
    
    # Save results to file
    output_file = output_dir / f's3_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    # Print summary
    print("\nAnalysis Summary:")
    print("================")

    
    # Print master account summary
    if CHECK_MASTER:
        Utility.print_account_summary("Master Account", results['master_account'])
        Utility.save_to_csv("master", results['master_account'], output_dir)

    # Print slave accounts summary
    for account_id, buckets in results['slave_accounts'].items():
        Utility.print_account_summary(f"Account: {account_id}", buckets)
        Utility.save_to_csv(account_id, buckets, output_dir)

    print(f"\nAll reports have been saved in directory: {output_dir}")
