#!/usr/bin/env python3


import boto3
import json
import time
import os
import sys
from time import sleep
from arnparse import arnparse
from datetime import datetime, timezone
from botocore.exceptions import ClientError




def assume_master_role(master_role_arn, session_name):
    """Assume Master role using instance profile credentials"""
    try:
        print(f"INFO: Attempting to assume Master role {master_role_arn}")
        master_account_id = arnparse(master_role_arn).account_id
        print(f"INFO: Master account ID extracted: {master_account_id}")
        
        base_session = boto3.Session()
        print(f"INFO: Created base session successfully")
        
        master_sts_client = base_session.client('sts')
        print(f"INFO: Created STS client for Master account {master_account_id} Role {master_role_arn} assumption")
        response = master_sts_client.assume_role(
                RoleArn=master_role_arn,
                RoleSessionName=session_name
        )

        if not response.get('Credentials'):
            print(f"ERROR: No credentials returned from Master assume role operation. Account {master_account_id} Role {master_role_arn}")
            sys.exit(1)

        # Create session with Master role credentials
        master_session = boto3.Session(
                aws_access_key_id=response['Credentials']['AccessKeyId'],
                aws_secret_access_key=response['Credentials']['SecretAccessKey'],
                aws_session_token=response['Credentials']['SessionToken']
        )

        # Verify the assumed role identity using the new session
        master_assumed_identity = master_session.client('sts').get_caller_identity()
        
        if  not master_assumed_identity or master_assumed_identity.get('Account') != master_account_id:
            print(f"CRITICAL: Assumed role account {master_assumed_identity.get('Account')} does not match Master account {master_account_id}")
            sys.exit(1)

        return master_session

    except Exception as e:
        print(f"ERROR: Unable to assume Master role {master_role_arn}: {str(e)}")
        sys.exit(1)
        

def assume_slave_role(slave_account_id, slave_role_name, session_name, master_role_arn, master_session=None):
    """
    Assume Slave role using Master role credentials with enhanced error handling and validation
    """
    try:
        print(f"INFO: Starting slave role assumption process for slave account {slave_account_id}")
        print(f"INFO: Target slave role: {slave_role_name}")
        
        # Get Master session if not provided
        if master_session is None:
            print(f"INFO: No master session provided, obtaining new master session")
            master_session = assume_master_role(master_role_arn = master_role_arn, session_name=session_name)
            
        if not master_session:
            print("ERROR: Failed to obtain Master session")
            sys.exit(1)

        # Create STS client with error retries
        master_sts_client = master_session.client('sts')

        slave_role_arn = f'arn:aws:iam::{slave_account_id}:role/{slave_role_name}'

        # Attempt to assume role with duration and tags
        response = master_sts_client.assume_role(
            RoleArn=slave_role_arn,
            RoleSessionName=session_name,
        )

        if not response.get('Credentials'):
            print(f"ERROR: No credentials returned from assume role operation. Account {slave_account_id} Role {slave_role_arn}")
            sys.exit(1)

        # Create session with temporary credentials
        slave_session = boto3.Session(
            aws_access_key_id=response['Credentials']['AccessKeyId'],
            aws_secret_access_key=response['Credentials']['SecretAccessKey'],
            aws_session_token=response['Credentials']['SessionToken']
        )

        # Verify the assumed role session
        slave_sts = slave_session.client('sts')
        assumed_identity = slave_sts.get_caller_identity()
        
        if assumed_identity.get('Account') != slave_account_id:
            print(f"CRITICAL: Assumed role account {assumed_identity.get('Account')} does not match Slave account {slave_account_id}")
            sys.exit(1)

        return slave_session
    except Exception as e:
        print(f"Unexpected Error: Unable to assume Slave role {slave_role_name} in account {slave_account_id}: {str(e)}")
        sys.exit(1)



def get_paginated_results(action, key, credentials, args=None):
    """Helper function to handle AWS pagination"""
    try:
        args = {} if args is None else args
        return [y for sublist in [x[key] for x in credentials.get_paginator(action).paginate(**args)]
                for y in sublist]
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"ERROR: AWS API error ({error_code}): {error_message}")
        raise e
    except KeyError as e:
        print(f"ERROR: Key '{key}' not found in response")
        raise e


def get_instance_profile_details(delete_role_name, slave_iam_client, slave_account_id):
    # STEP 4: Get and validate instance profiles
    try:
        instance_profiles = get_paginated_results(
            action='list_instance_profiles_for_role',
            key='InstanceProfiles',
            credentials=slave_iam_client,
            args={'RoleName': delete_role_name}
        )

        if instance_profiles is None:  # Ensure pagination didn't fail
            print(f"CRITICAL: Failed to get instance profiles for role {delete_role_name} in account {slave_account_id}")
            raise RuntimeError(f"Failed to retrieve instance profiles for role {delete_role_name} in account {slave_account_id}")

        # Required attributes for validation
        required_profile_attrs = [
            'Arn',
            'InstanceProfileName',
            'InstanceProfileId',
            'Path',
            'Roles'
        ]

        for profile in instance_profiles:
            if not all(attr in profile for attr in required_profile_attrs):
                print(f"CRITICAL: Incomplete instance profile information for role {delete_role_name} in account {slave_account_id}")
                raise ValueError(f"Incomplete instance profile information for role {delete_role_name} in account {slave_account_id}")

        return instance_profiles

    except Exception as e:
        print(f"CRITICAL: Error getting instance profiles for role {delete_role_name} in account {slave_account_id}: {str(e)}")
        raise Exception(f"Error in get_instance_profiles() at line {sys._getframe().f_lineno} for role {delete_role_name} in account {slave_account_id}: {str(e)}")


    

        


def get_inline_policy_details(delete_role_name, slave_iam_client, slave_account_id):
    # STEP: Get and validate ALL inline policies
    try:
        inline_policy_names = get_paginated_results(
            action='list_role_policies',
            key='PolicyNames',
            credentials=slave_iam_client,
            args={'RoleName': delete_role_name}
        )

        if inline_policy_names is None:  # Ensure pagination didn't fail
            print(f"CRITICAL: Failed to get inline policy names for role {delete_role_name} in account {slave_account_id}")
            raise RuntimeError(f"Failed to retrieve inline policy names for role {delete_role_name} in account {slave_account_id}")

        inline_policies = {}    

        for policy_name in inline_policy_names:
            try:
                policy_response = slave_iam_client.get_role_policy(
                    RoleName=delete_role_name,
                    PolicyName=policy_name
                )

                if not all(key in policy_response for key in ['PolicyName', 'PolicyDocument']):
                    print(f"CRITICAL: Incomplete inline policy response for policy {policy_name}, role {delete_role_name} in account {slave_account_id}")
                    raise ValueError(f"Incomplete inline policy response for policy {policy_name}, role {delete_role_name} in account {slave_account_id}")

                inline_policies[policy_name] = {}
                inline_policies[policy_name]['policy_document'] = policy_response['PolicyDocument']
            except Exception as e:
                print(f"CRITICAL: Failed to get inline policy {policy_name} for role {delete_role_name} in account {slave_account_id}: {e}")
                raise Exception(f"Error in get_inline_policy_details() at line {sys._getframe().f_lineno} for inline policy {policy_name} for role {delete_role_name} in account {slave_account_id}: {str(e)}")
        return inline_policies

    except Exception as e:
        print(f"CRITICAL: Error getting inline policies for role {delete_role_name} in account {slave_account_id}: {str(e)}")
        raise Exception(f"Error in get_inline_policy_details() at line {sys._getframe().f_lineno} for role {delete_role_name} in account {slave_account_id}: {str(e)}")


def get_attached_policy_details(delete_role_name, slave_iam_client, slave_account_id):
    # STEP: Get and validate ALL attached policies
    try:
        all_attached_policies = get_paginated_results(
            action='list_attached_role_policies',
            key='AttachedPolicies',
            credentials=slave_iam_client,
            args={'RoleName': delete_role_name}
        )

        if all_attached_policies is None:  # Ensure pagination didn't fail
            print(f"CRITICAL: Failed to get attached policies for role {delete_role_name} in account {slave_account_id}")
            raise RuntimeError(f"Failed to retrieve attached policies for role {delete_role_name} in account {slave_account_id}")

        role_details = {'aws_managed_policies' : {}, 'customer_managed_policies': {}}
        for policy in all_attached_policies:
            if not all(key in policy for key in ['PolicyArn', 'PolicyName']):
                print(f"CRITICAL: Incomplete policy information in attached policies for role {delete_role_name} in account {slave_account_id}")
                raise ValueError(f"Incomplete policy information in attached policies for role {delete_role_name} in account {slave_account_id}")

            policy_arn = policy['PolicyArn']
            policy_name = policy['PolicyName']
            try:
                # Get full policy details for customer managed policies
                policy_response = slave_iam_client.get_policy(PolicyArn=policy_arn)
                if 'Policy' not in policy_response:
                    print(f"CRITICAL: Invalid policy response for policy {policy_arn}, role {delete_role_name} in account {slave_account_id}")
                    raise ValueError(f"Invalid policy response for policy {policy_arn}, role {delete_role_name} in account {slave_account_id}")

                policy_version_id = policy_response['Policy']['DefaultVersionId']

                version_response = slave_iam_client.get_policy_version(
                    PolicyArn=policy_arn,
                    VersionId=policy_version_id
                )

                if ('PolicyVersion' not in version_response or
                    'Document' not in version_response['PolicyVersion']):
                    print(f"CRITICAL: Invalid policy version response for policy {policy_arn}, role {delete_role_name} in account {slave_account_id}")
                    raise ValueError(f"Invalid policy version response for policy {policy_arn}, role {delete_role_name} in account {slave_account_id}")

                policy_details = {
                    'policy_name': policy_name,
                    'policy_arn': policy_arn,
                    'policy_description': policy_response['Policy'].get('Description', ''),
                    'policy_tags': policy_response['Policy'].get('Tags', []),
                    'policy_document': version_response['PolicyVersion']['Document'],
                    'policy_default_version_id': policy_version_id,
                    'policy_id': policy_response['Policy']['PolicyId'],
                    'policy_path': policy_response['Policy']['Path'],
                    'policy_permissions_boundary_usage_count': policy_response['Policy']['PermissionsBoundaryUsageCount'],
                    'policy_create_date': policy_response['Policy']['CreateDate'],
                    'policy_raw_data': policy_response['Policy'] 
                }
            except Exception as e:
                print(f"CRITICAL: Failed to get customer managed policy details for policy {policy_arn}, role {delete_role_name} in account {slave_account_id}: {e}")
                raise Exception(f"Failed to get policy details for policy {policy_arn}, role {delete_role_name} in account {slave_account_id}: {e}")

            if policy_arn.startswith('arn:aws:iam::aws:'):
                role_details['aws_managed_policies'][policy_name] = policy_details
            else:
                role_details['customer_managed_policies'][policy_name] = policy_details
        return role_details
    except Exception as e:
        print(f"CRITICAL: Error processing attached policies for role {delete_role_name} in account {slave_account_id}: {str(e)}")
        raise Exception(f"Error processing attached policies for role {delete_role_name} in account {slave_account_id}: {str(e)}")





def get_tag_details(delete_role_name, slave_iam_client, slave_account_id):
    # STEP: Get and validate tags (considered critical for complete recovery)
    try:
        tags = get_paginated_results(
            action='list_role_tags',
            key='Tags',
            credentials=slave_iam_client,
            args={'RoleName': delete_role_name}
        )

        if tags is None:  # Ensure pagination didn't fail
            print(f"CRITICAL: Failed to get tags for role {delete_role_name} in account {slave_account_id}")
            raise RuntimeError(f"Failed to retrieve tags for role {delete_role_name} in account {slave_account_id}")

        return tags

    except Exception as e:
        print(f"CRITICAL: Error getting tags for role {delete_role_name} in account {slave_account_id}: {str(e)}")
        raise RuntimeError(f"Error getting tags for role {delete_role_name} in account {slave_account_id}: {str(e)}")




def check_role_deletion_criteria(delete_role_name, delete_role_details, slave_account_id, role_deletion_threshold_days):
    try:
        if not delete_role_details:
            print(f"ERROR: No role details provided for {delete_role_name} in account {slave_account_id}")
            raise ValueError(f"No role details provided for {delete_role_name} in account {slave_account_id}")

        current_time = datetime.now(timezone.utc)

        # Validate role name
        fetched_role_name = delete_role_details.get('RoleName')
        if not fetched_role_name or fetched_role_name != delete_role_name:
            print(f"CRITICAL: Role name mismatch in account {slave_account_id}. Expected: {delete_role_name}, Got: {fetched_role_name}")
            raise ValueError(f"Role name mismatch in account {slave_account_id}. Expected: {delete_role_name}, Got: {fetched_role_name}")

        # Check creation date
        create_date = delete_role_details.get('CreateDate')
        if not create_date:
            print(f"ERROR: Missing creation date for role {delete_role_name} in account {slave_account_id}")
            raise ValueError(f"Missing creation date for role {delete_role_name} in account {slave_account_id}")

        days_since_creation = (current_time - create_date).days
        print(f"------> {days_since_creation} day {create_date}, current {current_time}")
        print(f"INFO: Role {delete_role_name} in account {slave_account_id} was created {days_since_creation} days ago")

        # Get last usage information
        role_last_used = delete_role_details.get('RoleLastUsed', {})
        last_used_date = role_last_used.get('LastUsedDate')
        last_used_region = role_last_used.get('Region', 'N/A')

        # Case 1: Role is too new
        if days_since_creation <= role_deletion_threshold_days:
            print(f"INFO: Role {delete_role_name} in account {slave_account_id} is too new "
                  f"(created {days_since_creation} days ago, threshold: {role_deletion_threshold_days} days)")
            return False

        # Case 2: Role has never been used
        if not last_used_date:
            print(f"INFO: Role {delete_role_name} in account {slave_account_id}:")
            print(f"      - Created: {days_since_creation} days ago")
            print(f"      - Never been used")
            print(f"      - Meets deletion criteria (older than {role_deletion_threshold_days} days)")
            return True

        # Case 3: Role has been used
        days_since_last_use = (current_time - last_used_date).days
        print(f"INFO: Role {delete_role_name} in account {slave_account_id} last used:")
        print(f"      - {days_since_last_use} days ago")
        print(f"      - Region: {last_used_region}")

        # Case 3a: Role used recently
        if days_since_last_use < role_deletion_threshold_days:
            print(f"INFO: Role {delete_role_name} in account {slave_account_id} was used recently "
                  f"({days_since_last_use} days ago, threshold: {role_deletion_threshold_days} days)")
            return False

        # Case 3b: Role meets both age and usage criteria
        print(f"INFO: Role {delete_role_name} in account {slave_account_id} meets deletion criteria:")
        print(f"      - Created: {days_since_creation} days ago (threshold: {role_deletion_threshold_days} days)")
        print(f"      - Last used: {days_since_last_use} days ago (threshold: {role_deletion_threshold_days} days)")
        print(f"      - Last used region: {last_used_region}")
        return True

    except Exception as e:
        print(f"ERROR: Failed to check deletion criteria for role {delete_role_name} "
              f"in account {slave_account_id}: {str(e)}")
        raise Exception(f"Failed to check deletion criteria for role {delete_role_name} in account {slave_account_id}: {str(e)}")


def get_role_details(delete_role_name, slave_session, role_deletion_threshold_days, slave_account_id):
    print(f"INFO: Starting role details collection for role {delete_role_name} in account {slave_account_id}")
    print(f"INFO: Using deletion threshold of {role_deletion_threshold_days} days")

    try:
        # Initialize IAM client
        slave_iam_client = slave_session.client('iam')
        print(f"INFO: Created IAM client for slave account {slave_account_id}")

        # Get role information
        print(f"INFO: Retrieving role information for {delete_role_name} in account {slave_account_id}")
        try:
            role_response = slave_iam_client.get_role(RoleName=delete_role_name)
            print(f"INFO: Retrieved role information for {delete_role_name} in account {slave_account_id}")
        except slave_iam_client.exceptions.NoSuchEntityException:
            print(f"ERROR: Role {delete_role_name} not found in account {slave_account_id}")
            raise Exception(f"Role {delete_role_name} not found in account {slave_account_id}")
        except Exception as e:
            print(f"ERROR: Failed to retrieve role {delete_role_name}: {str(e)}")
            raise Exception(f"Failed to retrieve role {delete_role_name} in account {slave_account_id}")

        if not role_response or 'Role' not in role_response:
            print(f"CRITICAL: Invalid role response for {delete_role_name}")
            raise Exception(f"Invalid role response for {delete_role_name} in account {slave_account_id}")

        role = role_response['Role']

        # Validate required attributes
        required_role_attrs = [
            'Arn', 'RoleName', 'Path', 'RoleId', 'CreateDate',
            'AssumeRolePolicyDocument'
        ]

        if not all(attr in role for attr in required_role_attrs):
            print(f"CRITICAL: Missing required role attributes for {delete_role_name}")
            raise ValueError(f"Missing required attributes for role {delete_role_name} in account {slave_account_id}")


        # Verify deletion criteria first (no AWS API calls needed)
        try:
            if not check_role_deletion_criteria(
                delete_role_name=delete_role_name,
                delete_role_details=role,
                slave_account_id=slave_account_id,
                role_deletion_threshold_days=role_deletion_threshold_days
            ):
                print(f"INFO: Role {delete_role_name} does not meet deletion criteria in account {slave_account_id}")
                return False
        except Exception as e:
            print(f"ERROR: Failed to check deletion criteria for role {delete_role_name} in account {slave_account_id}: {str(e)}")
            return False

        # If role meets criteria, collect additional details
        try:
            inline_policies = get_inline_policy_details(
                delete_role_name=delete_role_name,
                slave_iam_client=slave_iam_client,
                slave_account_id=slave_account_id
            )
            attached_policies = get_attached_policy_details(
                delete_role_name=delete_role_name,
                slave_iam_client=slave_iam_client,
                slave_account_id=slave_account_id
            )
            instance_profiles = get_instance_profile_details(
                delete_role_name=delete_role_name,
                slave_iam_client=slave_iam_client,
                slave_account_id=slave_account_id
            )

            if any(detail is None for detail in [inline_policies, attached_policies, instance_profiles]):
                print(f"ERROR: Failed to collect complete policy details for role {delete_role_name}")
                return False

            # Complete role details with policy information
            complete_role_details = {
                'role_name': role['RoleName'],
                'role_arn': role['Arn'],
                'role_path': role['Path'],
                'role_id': role['RoleId'],
                'role_description': role.get('Description', ''),
                'role_create_date': role['CreateDate'],
                'role_trust_relationship': role['AssumeRolePolicyDocument'],
                'role_tags': role.get('Tags', []),
                'role_max_session': role.get('MaxSessionDuration', None),
                'role_permissions_boundary_arn': role.get('PermissionsBoundary', {}).get('PermissionsBoundaryArn', None),
                'role_permissions_boundary_type': role.get('PermissionsBoundary', {}).get('PermissionsBoundaryType', None),
                'role_last_used_date': role.get('RoleLastUsed', {}).get('LastUsedDate', None),
                'role_last_used_region': role.get('RoleLastUsed', {}).get('Region', None),
                'role_aws_managed_policies': attached_policies['aws_managed_policies'],
                'role_customer_managed_policies': attached_policies['customer_managed_policies'],
                'role_inline_policies': inline_policies,
                'role_instance_profiles': instance_profiles,
                'role_raw_data': role
            }

            print(f"INFO: Successfully collected all details for role {delete_role_name}")
            return complete_role_details

        except Exception as e:
            print(f"ERROR: Failed to collect policy details for role {delete_role_name}: {str(e)}")
            raise Exception(f"Failed to collect policy details for role {delete_role_name}: {str(e)}")

    except Exception as e:
        print(f"CRITICAL: Unexpected error processing role {delete_role_name}: {str(e)}")
        raise Exception(f"Unexpected error processing role {delete_role_name}: {str(e)}")



def write_json_to_file(json_data, slave_account_id, delete_role_name, workspace):
    if not all([json_data, slave_account_id, delete_role_name, workspace]):
        print("ERROR: All parameters (json_data, slave_account_id, delete_role_name, workspace) are required")
        return None
        
    try:
        # Create a timestamp for the filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create account specific directory path
        account_dir = os.path.join(workspace, slave_account_id, 'json')  # Fixed 'json' string
        
        # Sanitize filename components
        # Sanitize account ID and role name to ensure safe filename creation
        safe_account_id = re.sub(r'[^a-zA-Z0-9_-]', '_', str(slave_account_id))
        safe_role_name = re.sub(r'[^a-zA-Z0-9_-]', '_', str(delete_role_name))
        
        # Create directories if they don't exist
        try:
            os.makedirs(account_dir, exist_ok=True)
        except PermissionError as pe:
            print(f"ERROR: Permission denied while creating directory {account_dir}: {str(pe)}")
            return None
        
        # Create filename with account, role and timestamp
        filename = f"role_backup_{safe_account_id}_{safe_role_name}_{timestamp}.json"
        
        # Create full file path
        file_path = os.path.join(account_dir, filename)
        
        # Write JSON to file
        with open(file_path, 'w') as f:
            json.dump(json_data, f, indent=4, sort_keys=True, default=str)
            
        print(f"INFO: Successfully wrote role {delete_role_name} of account {slave_account_id} details to {file_path}")
        return file_path
    except IOError as io_err:
        print(f"ERROR: IO error while writing file for role {delete_role_name} of account {slave_account_id}: {str(io_err)}")
        return None
    except Exception as e:
        print(f"ERROR: Failed to write JSON to file for role {delete_role_name} of account {slave_account_id}: {str(e)}")
        return None

def zip_account_json_files(workspace, slave_account_id):
    if not workspace or not slave_account_id:
        print("ERROR: workspace and slave_account_id are required parameters")
        return None

    try:
        # Define paths
        account_dir = os.path.join(workspace, slave_account_id)
        json_dir = os.path.join(account_dir, 'json')
        zip_filename = f"role_backups_{slave_account_id}.zip"
        zip_path = os.path.join(account_dir, zip_filename)
        
        # Validate workspace and account directory
        if not os.path.exists(workspace):
            print(f"ERROR: Workspace directory does not exist: {workspace}, while working on {slave_account_id}")
            return None
            
        if not os.path.exists(account_dir):
            print(f"ERROR: Account directory does not exist: {account_dir}, while working on {slave_account_id}")
            return None

        # Check if JSON directory exists and has files
        if not os.path.exists(json_dir):
            print(f"WARNING: No JSON directory found for account {slave_account_id}")
            return None
            
        try:
            json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
        except OSError as e:
            print(f"ERROR: Failed to list JSON directory contents while working on {slave_account_id}: {str(e)}")
            return None
            
        if not json_files:
            print(f"WARNING: No JSON files found for account {slave_account_id}")
            return None
            
        # Create zip file
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for json_file in json_files:
                    file_path = os.path.join(json_dir, json_file)
                    # Verify file exists and is readable
                    if not os.path.isfile(file_path):
                        print(f"WARNING: File not found or not accessible: {file_path}")
                        continue
                    try:
                        arcname = os.path.join('json', json_file)  # Preserve directory structure in zip
                        zipf.write(file_path, arcname)
                    except (OSError, zipfile.BadZipFile) as e:
                        print(f"ERROR: Failed to add file to zip: {file_path}: {str(e)}")
                        continue
        except (OSError, zipfile.BadZipFile) as e:
            print(f"ERROR: Failed to create zip file: {str(e)}")
            # Clean up partial zip file if it exists
            if os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except OSError:
                    pass
            return None
                
        # Verify the zip file was created successfully
        if not os.path.exists(zip_path):
            print(f"ERROR: Zip file was not created at {zip_path}")
            return None
            
        print(f"INFO: Successfully created zip file for account {slave_account_id} at {zip_path}")
        return zip_path
        
    except Exception as e:
        print(f"ERROR: Unexpected error while creating zip file for account {slave_account_id}: {str(e)}")
        # Clean up partial zip file if it exists
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except OSError:
                pass
        return None

def upload_file_s3(bucket_name, file_name, file_content, max_retries = 3):
    for attempt in range(max_retries):
        try:
            s3 = boto3.client('s3', region_name='ap-northeast-2')
            s3.put_object(Bucket=bucket_name, Key=file_name, Body=file_content)
            print(f"INFO: Successfully uploaded {file_name} to {bucket_name}")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                print(f"ERROR: Bucket {bucket_name} does not exist")
                return False
            elif error_code == 'AccessDenied':
                print(f"ERROR: Access denied to bucket {bucket_name}")
                return False
            print(f"ERROR: Failed to upload to S3 (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                return False
            time.sleep(2 ** attempt)
    return False



def read_parameter(param_name):
    if not param_name:
        print("ERROR: Parameter name cannot be empty")
        sys.exit(1)

    try:
        param_value = os.environ.get(param_name, '').strip()
        print(f"INFO: {param_name} = {param_value}")
        if not param_value:
            print(f"WARNING: Parameter '{param_name}' is empty or not set")
        return param_value

    except Exception as e:
        print(f"ERROR: Failed to read parameter '{param_name}': {str(e)}")
        sys.exit(1)


def read_account_file(file):
    if not file:
        print("ERROR: Parameter File cannot be empty")
        sys.exit(1)
    try:
        account_all = {}
        with open(file, 'r') as account_file:
            for line_num, line in enumerate(account_file, 1):
                # Skip empty lines
                line = line.strip()
                if not line:
                    continue

                line = [item.strip() for item in line.split(',')]
                if len(line) < 2:
                    print(f"ERROR: Invalid format at line {line_num}. Expected 'account,role'")
                    sys.exit(1)
                account = line[0]
                role = line[1]

                # Validate account ID
                if not account or (not account.isdigit() or len(account) != 12):
                    print(f"ERROR: Invalid AWS account ID '{account}' at line {line_num}. Must be 12 digits")
                    sys.exit(1)
                
                
                # Validate role
                if not role:
                    print(f"ERROR: AWS account ID '{account}' has empty role at line {line_num}")
                    sys.exit(1)

                account_all.setdefault(account, []).append(role)
        if not account_all:
            print(f"ERROR: No valid entries found in file '{file}'")
            sys.exit(1)

        print(f"INFO: Successfully read {len(account_all)} accounts from '{file}'")
        return account_all
    except Exception as e:
        print(f"ERROR: Failed to read account file '{file}': {str(e)}")
        sys.exit(1)




def remove_instance_profiles(delete_role_name, instance_profiles, slave_iam_client, slave_account_id):
    """Remove all instance profile associations"""
    try:
        for profile in instance_profiles:
            profile_name = profile.get('InstanceProfileName')
            if profile_name:
                print(f"INFO: Removing role {delete_role_name} from instance profile {profile_name} in account {slave_account_id}")
                try:
                    slave_iam_client.remove_role_from_instance_profile(
                        InstanceProfileName=profile_name,
                        RoleName=delete_role_name
                    )
                    slave_iam_client.delete_instance_profile(InstanceProfileName=profile_name)
                except Exception as e:
                    print(f"WARNING: Error removing instance profile {profile_name} from role {delete_role_name} in account {slave_account_id}: {str(e)}")
                    raise Exception(f"Failed to remove instance profile {profile_name} from role {delete_role_name} in account {slave_account_id}: {str(e)}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to remove instance profiles from role {delete_role_name} in account {slave_account_id}: {str(e)}")
        raise Exception(f"Failed to remove instance profiles from role {delete_role_name} in account {slave_account_id}: {str(e)}")

def detach_managed_policies(delete_role_name, policy_details, slave_iam_client, policy_type, slave_account_id):
    """Detach AWS managed or customer managed policies"""
    try:
        for policy_name, policy_info in policy_details.items():
            try:
                policy_arn = policy_info.get('policy_arn')
                if policy_arn:
                    print(f"INFO: Detaching {policy_type} policy {policy_name} from role {delete_role_name} in account {slave_account_id}")
                    slave_iam_client.detach_role_policy(
                        RoleName=delete_role_name,
                        PolicyArn=policy_arn
                    )
            except Exception as e:
                print(f"WARNING: Error detaching {policy_type} policy {policy_name} from role {delete_role_name} in account {slave_account_id}: {str(e)}")
                raise Exception(f"Failed to detach {policy_type} policy {policy_name} from role {delete_role_name} in account {slave_account_id}: {str(e)}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to detach {policy_type} policies from role {delete_role_name} in account {slave_account_id}: {str(e)}")
        raise Exception(f"Failed to detach {policy_type} policies from role {delete_role_name} in account {slave_account_id}: {str(e)}")

def delete_inline_policies(delete_role_name, inline_policies, slave_iam_client, slave_account_id):
    """Delete all inline policies"""
    try:
        for policy_name in inline_policies.keys():
            try:
                print(f"INFO: Deleting inline policy {policy_name} from role {delete_role_name} in account {slave_account_id}")
                slave_iam_client.delete_role_policy(
                    RoleName=delete_role_name,
                    PolicyName=policy_name
                )
            except Exception as e:
                print(f"WARNING: Error deleting inline policy {policy_name} from role {delete_role_name} in account {slave_account_id}: {str(e)}")
                raise Exception(f"Failed to delete inline policy {policy_name} from role {delete_role_name} in account {slave_account_id}: {str(e)}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to delete inline policies from role {delete_role_name} in account {slave_account_id}: {str(e)}")
        raise Exception(f"Failed to delete inline policies from role {delete_role_name} in account {slave_account_id}: {str(e)}")


def verify_role_deletion(delete_role_name, slave_iam_client, slave_account_id):
    """Verify that the role has been deleted"""
    print(f"INFO: Starting verification of role deletion for {delete_role_name} in account {slave_account_id}")
    try:
        print(f"INFO: Attempting to retrieve deleted role ({delete_role_name}) to verify deletion for account {slave_account_id}")
        slave_iam_client.get_role(RoleName=delete_role_name)
        print(f"ERROR: Role {delete_role_name} in account {slave_account_id} still exists after deletion attempt")
        return False
    except slave_iam_client.exceptions.NoSuchEntityException:
        print(f"SUCCESS: Role {delete_role_name} in account {slave_account_id} successfully deleted")
        return True
    except Exception as e:
        print(f"ERROR: Failed to verify role {delete_role_name} deletion for account {slave_account_id}: {str(e)}")
        return False

def delete_role_safely(delete_role_name, delete_role_details, slave_session, role_deletion_threshold_days, slave_account_id):
    if not delete_role_details:
        print(f"ERROR: No role details provided for role {delete_role_name} deletion in account {slave_account_id}")
        return False

    try:
        fetched_role_name = delete_role_details.get('role_name')
        if not fetched_role_name or fetched_role_name != delete_role_name:
            print(f"ERROR: Role name {delete_role_name} not found in details for account {slave_account_id}")
            return False

        
        # Verify deletion criteria first (no AWS API calls needed)
        try:
            if not check_role_deletion_criteria(
                delete_role_name=delete_role_name,
                delete_role_details=delete_role_details['role_raw_data'],
                slave_account_id=slave_account_id,
                role_deletion_threshold_days=role_deletion_threshold_days
            ):
                print(f"INFO: Role {delete_role_name} does not meet deletion criteria in account {slave_account_id}")
                return False
        except Exception as e:
            print(f"ERROR: Failed to check deletion criteria for role {delete_role_name} in account {slave_account_id}: {str(e)}")
            return False

        # Create IAM client only if role meets deletion criteria
        try:
            slave_iam_client = slave_session.client('iam')
        except Exception as e:
            print(f"ERROR: Failed to create IAM client for account {slave_account_id} while checking role {delete_role_name}: {str(e)}")
            return False


        
        # Sequential cleanup with proper error handling
        cleanup_steps = [
            {
                'action': lambda: remove_instance_profiles(
                    delete_role_name=delete_role_name,
                    instance_profiles=delete_role_details.get('role_instance_profiles', []),
                    slave_iam_client=slave_iam_client,
                    slave_account_id=slave_account_id
                ),
                'description': 'Remove instance profiles'
            },
            {
                'action': lambda: detach_managed_policies(
                    delete_role_name=delete_role_name,
                    policy_details=delete_role_details.get('role_aws_managed_policies', {}),
                    slave_iam_client=slave_iam_client,
                    policy_type='AWS managed',
                    slave_account_id=slave_account_id
                ),
                'description': 'Detach AWS managed policies'
            },
            {
                'action': lambda: detach_managed_policies(
                    delete_role_name=delete_role_name,
                    policy_details=delete_role_details.get('role_customer_managed_policies', {}),
                    slave_iam_client=slave_iam_client,
                    policy_type='customer managed',
                    slave_account_id=slave_account_id
                ),
                'description': 'Detach customer managed policies'
            },
            {
                'action': lambda: delete_inline_policies(
                    delete_role_name=delete_role_name,
                    inline_policies=delete_role_details.get('role_inline_policies', {}),
                    slave_iam_client=slave_iam_client,
                    slave_account_id=slave_account_id
                ),
                'description': 'Delete inline policies'
            }
        ]

        # Execute cleanup steps
        for step in cleanup_steps:
            try:
                if not step['action']():
                    print(f"ERROR: Failed to {step['description']} for role {delete_role_name} in account {slave_account_id}")
                    return False
            except Exception as e:
                print(f"ERROR: {step['description']} failed for role {delete_role_name} in account {slave_account_id}: {str(e)}")
                return False

        # Delete the role
        try:
            print(f"INFO: Deleting role {delete_role_name} in account {slave_account_id}")
            slave_iam_client.delete_role(RoleName=delete_role_name)
        except Exception as e:
            print(f"ERROR: Failed to delete role {delete_role_name} in account {slave_account_id}: {str(e)}")
            return False

        # Verify deletion
        try:
            if verify_role_deletion(
                delete_role_name=delete_role_name,
                slave_iam_client=slave_iam_client,
                slave_account_id=slave_account_id
            ):
                print(f"SUCCESS: Role {delete_role_name} successfully deleted in account {slave_account_id}")
                return True
            else:
                print(f"ERROR: Could not verify deletion of role {delete_role_name} in account {slave_account_id}")
                return False
        except Exception as e:
            print(f"ERROR: Failed to verify role {delete_role_name} deletion in account {slave_account_id}: {str(e)}")
            return False

    except Exception as e:
        print(f"ERROR: Unexpected error deleting role {delete_role_name} in account {slave_account_id}: {str(e)}")
        return False




if __name__ == '__main__':
    # Read parameters from Jenkins build
    account_id = read_parameter('Account')
    build_number = read_parameter('BUILD_NUMBER')
    workspace = read_parameter('WORKSPACE')
    master_role_arn = f"arn:aws:iam::038462757316:role/cia_master_management_terraform_role-v2"
    slave_role_name = "cloud_management_terraform-ec2-role-v2"
    session_name = f"CIA-Terraform-Pipeline--PR-CHECK--{build_number}"
    role_deletion_threshold_days = 25
    task = read_parameter('Task', 'backup')
    
    
    if account_id.lower() == 'all':
        file = read_parameter('File')
        file_path = os.path.join(workspace, file)
        account_mappings = read_account_file(file_path)
        print(f"INFO: Processing ALL accounts from file: {file_path}")
    elif account_id.isdigit() and len(account_id) == 12:
        role_name = read_parameter('Role')
        if not role_name:
            print(f"ERROR: Role parameter is missing for account ID: {account_id}")
            sys.exit(1)
        account_mappings = {account_id : [role_name]}
        print(f"INFO: Given ONLY account ID: {account_id} to delete role name: {role_name}")
    else:
        print(f"INFO: Invalid account ID: {account_id}")
        sys.exit(1)

    master_session = assume_master_role(master_role_arn= master_role_arn, session_name=session_name)
 
    for slave_account_id, delete_roles in account_mappings.items():
        try:
            slave_session = assume_slave_role(slave_account_id=slave_account_id, slave_role_name=slave_role_name, 
                                           session_name=session_name, master_role_arn=master_role_arn, 
                                           master_session=master_session)
            if not slave_session:
                print(f"ERROR: Failed to assume role for slave account {slave_account_id}. Skipping deletion on this account.....")
                continue

            for delete_role_name in delete_roles:
                try:
                    if delete_role_name in [slave_role_name, arnparse(master_role_arn).resource]:
                        print(f"CRITICAL: Skipping Role {delete_role_name}. You cannot delete Role: {arnparse(master_role_arn).resource} and Role: {slave_role_name}")
                        continue
                    
                    print(f"INFO: Processing slave account ID: {slave_account_id} to delete role name role: {delete_role_name}")
                    
                    try:
                        delete_role_details = get_role_details(delete_role_name=delete_role_name, slave_session=slave_session, role_deletion_threshold_days=role_deletion_threshold_days, slave_account_id=slave_account_id)
                        if not delete_role_details:
                            print(f"INFO: Skipping deletion for Account {slave_account_id} Role {delete_role_name} due to missing details or threshold not met.")
                            continue
                        else:
                            print(f"SUCCESS: Role {delete_role_name} in account {slave_account_id} read successfully.")
                            json_output = json.dumps(delete_role_details, indent=3, sort_keys=True, ensure_ascii=False, default=str)
                                
                            # Write the JSON output to a file
                            backup_file = write_json_to_file(
                                    json_data=delete_role_details,
                                    slave_account_id=slave_account_id,
                                    delete_role_name=delete_role_name,
                                    workspace=workspace
                            )
                            if not backup_file:
                                print(f"ERROR: Failed to backup role {delete_role_name} in account {slave_account_id}. Skipping Deletion for safety.....")
                                continue
                                
                            print(f"INFO: Role backup for role {delete_role_name} in account {slave_account_id} is saved to {backup_file}")
                            
                            # Verify backup file exists and is not empty
                            if not os.path.exists(backup_file) or os.path.getsize(backup_file) == 0:
                                print(f"ERROR: Backup file verification failed for role {delete_role_name} in account {slave_account_id}. Skipping Deletion for safety.....")
                                continue
                                
                            try:
                                # Verify backup file contains valid JSON
                                with open(backup_file, 'r') as f:
                                    backup_content = json.load(f)
                                if not backup_content:
                                    print(f"ERROR: Backup file is empty or invalid for role {delete_role_name} in account {slave_account_id}. Skipping Deletion for safety.....")
                                    continue

                                # Upload backup to S3 before deletion
                                s3_bucket = "your-backup-bucket-name"  # Replace with your S3 bucket name
                                s3_key = f"role_backups/{slave_account_id}/{os.path.basename(backup_file)}"
                                
                                try:
                                    with open(backup_file, 'rb') as f:
                                        s3_upload_success = upload_file_s3(
                                            bucket_name=s3_bucket,
                                            file_name=s3_key,
                                            file_content=f.read()
                                        )
                                    
                                    if not s3_upload_success:
                                        print(f"ERROR: Failed to upload backup to S3 for role {delete_role_name} in account {slave_account_id}. Skipping deletion for safety...")
                                        continue
                                        
                                    print(f"SUCCESS: Role backup uploaded to s3://{s3_bucket}/{s3_key}")
                                    
                                    # Proceed with deletion only after successful backup and upload
                                    if delete_role_details and backup_file and backup_content and s3_upload_success and task == 'delete':
                                        deletion_success = delete_role_safely(
                                            delete_role_name=delete_role_name,
                                            delete_role_details=delete_role_details,
                                            slave_session=slave_session,
                                            role_deletion_threshold_days=role_deletion_threshold_days,
                                            slave_account_id=slave_account_id
                                        )
                                    
                                        if not deletion_success:
                                            print(f"WARNING: Role deletion failed for role {delete_role_name} in account {slave_account_id} but backup exists in S3: s3://{s3_bucket}/{s3_key}")
                                        
                                except Exception as e:
                                    print(f"ERROR: Failed to upload backup to S3 for role {delete_role_name} in account {slave_account_id}: {str(e)}")
                                    continue
                            except Exception as e:
                                print(f"ERROR: Failed to delete role {delete_role_name} safely for account {slave_account_id}: {str(e)}")

                    except Exception as e:
                        print(f"ERROR: Failed to get role {delete_role_name} details for account {slave_account_id}: {str(e)}")
                        
                except Exception as e:
                    print(f"ERROR: Failed to process role {delete_role_name} in account {slave_account_id}: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"ERROR: Failed to assume slave Role {slave_role_name} in Account {slave_account_id}: {str(e)}")
            continue
        
        # After processing all roles for this account, create zip file
        try:
            zip_path = zip_account_json_files(workspace, slave_account_id)
            if zip_path:
                print(f"SUCCESS: Created zip archive for account {slave_account_id} at {zip_path}")
            else:
                print(f"WARNING: No zip archive created for account {slave_account_id}")
        except Exception as e:
            print(f"ERROR: Failed to create zip archive for account {slave_account_id}: {str(e)}")
 



