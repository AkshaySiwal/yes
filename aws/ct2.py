import boto3
import os
import sys
import csv


def assume_master_role(master_role_arn, session_name):
    """Assume Master role using instance profile credentials"""
    try:
        print(f"INFO: Attempting to assume Master role {master_role_arn}")
        master_account_id = master_role_arn.split(':')[4]
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




def get_trail_event_selectors(slave_session, result):
    try:
        for region, trails in result.items():
            slave_cloudtrail = slave_session.client('cloudtrail', region_name=region)
            for trail in trails:
                try:
                    try:
                        cia_team_trail = 'No'
                        trail_role_tag_value = 'Not Found'
                        tags_response = slave_cloudtrail.list_tags(ResourceIdList=[trail['trail_arn']])
                        tags = {}
                        for resource in tags_response.get('ResourceTagList', []):
                            if resource['ResourceId'] == trail['trail_arn']:
                                for tag in resource.get('TagsList', []):
                                    tags[tag['Key']] = tag['Value']
                                    if tag['Key'].lower() == 'role':
                                        trail_role_tag_value = tag['Value']
                                        if 'cia' in tag['Value'].lower():
                                            cia_team_trail = 'Yes'

                        if trail_role_tag_value == 'Not Found':
                            cia_team_trail = 'Yes'
                    except Exception as e:
                        print(f"ERROR: Listing tags for trail {trail['trail_arn']} failed: {e}")
                        trail['comments'] = 'Error finding tags'
                    
                    trail['trail_role_tag_value'] = trail_role_tag_value
                    trail['cia_team_trail'] = cia_team_trail
                    trail['trail_tags'] = tags

                    try:
                        status = slave_cloudtrail.get_trail_status(Name=trail['trail_arn'])
                        trail_status = status.get('IsLogging', 'Error')
                    except Exception as e:
                        print(f"ERROR: Unable to get trail status for {trail['trail_name']}: {str(e)}")
                        trail['comments'] = 'Error finding trail status'
                    selectors = slave_cloudtrail.get_event_selectors(TrailName=trail['trail_name'])

                    has_management_events = False
                    has_data_events = False
                    management_events_read_write = "NA"
                    data_events_read_write = "NA"


                    # Check EventSelectors
                    for selector in selectors.get('EventSelectors', []):
                    # Check for management events
                        if selector.get('IncludeManagementEvents', False):
                            has_management_events = True
                            management_events_read_write = selector.get('ReadWriteType', 'NA')

                        # Check for data events
                        if selector.get('DataResources', []):
                            has_data_events = True

                        # Check Advanced Event Selectors (newer method)
                    advanced_selectors = selectors.get('AdvancedEventSelectors', [])
                    if advanced_selectors:
                        for selector in advanced_selectors:
                            field_selectors = selector.get('FieldSelectors', [])
                            for field in field_selectors:
                                if field.get('Field') == 'eventCategory':
                                    if 'Management' in field.get('Equals', []):
                                        has_management_events = True
                                    if 'Data' in field.get('Equals', []):
                                        has_data_events = True
                                    
                            for field in field_selectors:
                                if has_management_events:
                                    if field.get('Field') == 'readOnly':
                                        if 'true' in field.get('Equals', []):
                                            management_events_read_write = "ReadOnly"
                                        elif 'false' in field.get('Equals', []):
                                            management_events_read_write = "WriteOnly"
                                        else:
                                            management_events_read_write = "All"
                                if has_data_events:
                                    if field.get('Field') == 'readOnly':
                                        if 'true' in field.get('Equals', []):
                                            data_events_read_write =  "ReadOnly"
                                        elif 'false' in field.get('Equals', []):
                                            data_events_read_write = "WriteOnly"
                                        else:
                                            data_events_read_write = "All"
                            if has_data_events and data_events_read_write not in ["ReadOnly", "WriteOnly"]:
                                data_events_read_write = "All"
                            if has_management_events and management_events_read_write not in ["ReadOnly", "WriteOnly"]:
                                management_events_read_write = "All"
   


                            
                    trail['has_management_events'] = has_management_events
                    trail['has_data_events'] = has_data_events
                    trail['management_events_read_write'] = management_events_read_write
                    trail['data_events_read_write'] = data_events_read_write
                    trail['trail_status'] = trail_status
                except Exception as e:
                    print(f"ERROR: Exception occurred while processing event selectors of trail {trail['Name']}: {str(e)}")
                    continue
    except Exception as e:
        _, _, tb = sys.exc_info()
        lineno = tb.tb_lineno if tb else 'unknown'
        print(f"ERROR: Unable to find event selector details for trail of region {region}, Exception occurred at line {lineno}: {str(e)}")
    
    return result





def analyze_cloudtrail_costs(slave_session):
    slave_cloudtrail = slave_session.client('cloudtrail')

    response = slave_cloudtrail.describe_trails(includeShadowTrails=True)


    result = {}

    for trail in response['trailList']:
        row = {}
        row['trail_name'] = trail['Name']
        row['is_multi_region'] = trail['IsMultiRegionTrail']
        row['trail_arn'] = trail['TrailARN']
        row['include_global_service_events'] = trail['IncludeGlobalServiceEvents']
        row['trail_arn'] = trail['TrailARN']
        row['trail_s3_bucket'] = trail['S3BucketName']
        row['has_custome_event_selector'] = trail['HasCustomEventSelectors']
        row['has_insight_selector'] = trail['HasInsightSelectors']
        row['is_organization_trail'] = trail['IsOrganizationTrail']
        home_region = trail['HomeRegion'] 

        
        
        if not result.get(home_region):
            result[home_region] = []
        
        result[home_region].append(row)


    # Get event selector information
    result = get_trail_event_selectors(slave_session, result)
    return result



def trails_to_csv(trails_data, output_file='trails.csv'):
    # Get all possible fields from the trail dictionaries
    fields = set()
    for account, regions in trails_data.items():
        for region, trails in regions.items():
            for trail in trails:
                fields.update(trail.keys())

    # Remove fields that will be handled separately to avoid duplicates
    fields = fields - {'trail_name', 'trail_status', 'cia_team_trail', 'trail_role_tag_value', 'trail_s3_bucket', 'has_data_events', 'data_events_read_write', 'has_management_events', 'management_events_read_write', 'has_insight_selector', 'is_multi_region', 'is_organization_trail', 'trail_tags', 'comments'}

    # Define column order with unique columns
    base_columns = ['account', 'trail_name', 'trail_status', 'region', 'cia_team_trail', 'trail_role_tag_value', 'trail_s3_bucket', 'has_data_events', 'data_events_read_write', 'has_management_events', 'management_events_read_write', 'has_insight_selector', 'is_multi_region', 'is_organization_trail']
    remaining_columns = sorted(list(fields))
    remaining_columns.append('trail_tags')
    remaining_columns.append('comments')

    # Create final headers list with no duplicates
    headers = []
    seen = set()

    # Add columns while checking for duplicates
    for column in base_columns + remaining_columns:
        if column not in seen and column.strip():  # Check if column name is not empty
            headers.append(column)
            seen.add(column)

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()

        # Write each trail
        for account, regions in trails_data.items():
            for region, trails in regions.items():
                for trail in trails:
                    # Create row with basic info
                    row = {
                        'account': account,
                        'region': region
                    }

                    # Add trail properties, handling any potential missing fields
                    for key, value in trail.items():
                        if key in headers:  # Only add if column exists in headers
                            row[key] = value

                    writer.writerow(row)

    print(f"CSV file '{output_file}' has been created")



def get_s3_bucket_tags(s3_client, bucket_name):
    """Get tags for a specific S3 bucket with error handling"""
    try:
        tags_response = s3_client.get_bucket_tagging(Bucket=bucket_name)
        tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagSet', [])}
        role_tag_value = 'Not Found'
        for tag in tags_response.get('TagSet', []):
            if tag['Key'].lower() == 'role':
                role_tag_value = tag['Value']
                break
        cia_team_bucket = 'Yes' if 'cia' in role_tag_value.lower() else 'No'
        if role_tag_value == 'Not Found':
            cia_team_bucket = 'Yes'
        return tags, role_tag_value, cia_team_bucket
    except s3_client.exceptions.NoSuchTagSet:
        return {}, 'Not Found', 'Yes'
    except Exception as e:
        print(f"ERROR: Unable to get tags for bucket {bucket_name}: {str(e)}")
        return {}, 'Error checking Bucket tags', 'Error checking Bucket tags'


def get_s3_logging_status(s3_client, bucket_name):
    """Get S3 bucket logging status"""
    try:
        logging = s3_client.get_bucket_logging(Bucket=bucket_name)
        if logging.get('LoggingEnabled'):
            target_bucket = logging['LoggingEnabled'].get('TargetBucket', '')
            target_prefix = logging['LoggingEnabled'].get('TargetPrefix', '')
            return {
                'logging_enabled': 'Enabled',
                'target_bucket': target_bucket,
                'target_prefix': target_prefix
            }
        return {
            'logging_enabled': 'Disabled',
            'target_bucket': '',
            'target_prefix': ''
        }
    except Exception as e:
        print(f"ERROR: Unable to get logging status for bucket {bucket_name}: {str(e)}")
        return {
            'logging_enabled': 'Error check bucket logging status',
            'target_bucket': 'Error check bucket logging status',
            'target_prefix': 'Error check bucket logging status',
        }

def analyze_s3_buckets(slave_session):
    """Analyze S3 buckets and their configurations"""
    try:
        s3_client = slave_session.client('s3')
        result = []

        # List all buckets
        response = s3_client.list_buckets()

        for bucket in response['Buckets']:
            bucket_name = bucket['Name']
            bucket_info = {
                'bucket_name': bucket_name,
                'creation_date': bucket['CreationDate'].isoformat(),
                'bucket_region': 'Unknown',
                'versioning': 'Unknown',
                'lifecycle_rules': 'Unknown',
                'encryption': 'Unknown',
                'server_access_logging': 'Unknown',
                'logging_target_bucket': '',
                'logging_target_prefix': '',
                'comments': ''
            }

            try:
                # Get bucket location
                location = s3_client.get_bucket_location(Bucket=bucket_name)
                bucket_info['bucket_region'] = location.get('LocationConstraint') or 'us-east-1'

                # Get bucket tags
                tags, role_tag_value, cia_team_bucket = get_s3_bucket_tags(s3_client, bucket_name)
                bucket_info['bucket_tags'] = tags
                bucket_info['bucket_role_tag_value'] = role_tag_value
                bucket_info['cia_team_bucket'] = cia_team_bucket

                # Get versioning status
                versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
                bucket_info['versioning'] = versioning.get('Status', 'Disabled')

                # Get lifecycle rules
                try:
                    lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
                    bucket_info['lifecycle_rules'] = len(lifecycle.get('Rules', []))
                except s3_client.exceptions.NoSuchLifecycleConfiguration:
                    bucket_info['lifecycle_rules'] = 0

                
                # Get encryption configuration
                try:
                    encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
                    bucket_info['encryption'] = encryption['ServerSideEncryptionConfiguration']['Rules'][0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
                except:
                    bucket_info['encryption'] = 'Not configured'


                # Get server access logging status
                logging_status = get_s3_logging_status(s3_client, bucket_name)
                bucket_info['server_access_logging'] = logging_status['logging_enabled']
                bucket_info['logging_target_bucket'] = logging_status['target_bucket']
                bucket_info['logging_target_prefix'] = logging_status['target_prefix']


            except Exception as e:
                bucket_info['comments'] = f"Error processing bucket details: {str(e)}"

            result.append(bucket_info)

        return result

    except Exception as e:
        print(f"ERROR: Unable to analyze S3 buckets: {str(e)}")
        return []




def s3_to_csv(s3_data, output_file='s3_buckets.csv'):
    """Export S3 bucket information to CSV"""
    # Define column order
    headers = [
        'account',
        'bucket_name',
        'bucket_region',
        'creation_date',
        'cia_team_bucket',
        'bucket_role_tag_value',
        'versioning',
        'lifecycle_rules',
        'encryption',
        'server_access_logging',
        'logging_target_bucket',
        'logging_target_prefix',
        'bucket_tags',
        'comments'
    ]

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()

        for account, buckets in s3_data.items():
            for bucket in buckets:
                row = {'account': account}
                row.update(bucket)
                writer.writerow(row)

    print(f"CSV file '{output_file}' has been created")





def check_s3_object_monitoring(slave_session, bucket_name=None):
    """
    Check if S3 object-level monitoring is enabled for specific or all buckets
    Returns dictionary of buckets with their monitoring status and details
    """
    try:
        cloudtrail = slave_session.client('cloudtrail')
        monitored_buckets = {}

        # Get all trails
        trails = cloudtrail.describe_trails(includeShadowTrails=True)

        for trail in trails['trailList']:
            trail_name = trail['Name']
            trail_arn = trail['TrailARN']

            try:
                # Get event selectors
                selectors = cloudtrail.get_event_selectors(TrailName=trail_name)

                # Check traditional event selectors
                for selector in selectors.get('EventSelectors', []):
                    for data_resource in selector.get('DataResources', []):
                        if data_resource.get('Type') == 'AWS::S3::Object':
                            for value in data_resource.get('Values', []):
                                # Extract bucket name from ARN
                                bucket_arn = value.split('/')
                                monitored_bucket = bucket_arn[0].split(':')[-1]

                                if bucket_name and bucket_name != monitored_bucket:
                                    continue

                                if monitored_bucket not in monitored_buckets:
                                    monitored_buckets[monitored_bucket] = {
                                        'monitoring_enabled': True,
                                        'monitoring_trails': [],
                                        'read_write_type': set(),
                                        'selector_type': 'Traditional'
                                    }

                                monitored_buckets[monitored_bucket]['monitoring_trails'].append({
                                    'trail_name': trail_name,
                                    'trail_arn': trail_arn,
                                    'read_write_type': selector.get('ReadWriteType', 'All')
                                })
                                monitored_buckets[monitored_bucket]['read_write_type'].add(
                                    selector.get('ReadWriteType', 'All')
                                )

                # Check advanced event selectors
                for selector in selectors.get('AdvancedEventSelectors', []):
                    is_s3_data_event = False
                    read_write_type = 'All'

                    for field_selector in selector.get('FieldSelectors', []):
                        # Check if this is an S3 data event
                        if (field_selector.get('Field') == 'eventCategory' and
                            'Data' in field_selector.get('Equals', [])):
                            is_s3_data_event = True

                        # Check if this is specifically for S3 objects
                        if (field_selector.get('Field') == 'resources.type' and
                            'AWS::S3::Object' in field_selector.get('Equals', [])):
                            is_s3_data_event = True

                        # Get read/write type
                        if field_selector.get('Field') == 'readOnly':
                            if 'true' in field_selector.get('Equals', []):
                                read_write_type = 'ReadOnly'
                            elif 'false' in field_selector.get('Equals', []):
                                read_write_type = 'WriteOnly'

                        # Get specific bucket if defined
                        if field_selector.get('Field') == 'resources.ARN':
                            for value in field_selector.get('StartsWith', []):
                                bucket_name_from_arn = value.split(':')[-1]
                                if bucket_name and bucket_name != bucket_name_from_arn:
                                    continue

                                if bucket_name_from_arn not in monitored_buckets:
                                    monitored_buckets[bucket_name_from_arn] = {
                                        'monitoring_enabled': True,
                                        'monitoring_trails': [],
                                        'read_write_type': set(),
                                        'selector_type': 'Advanced'
                                    }

                                monitored_buckets[bucket_name_from_arn]['monitoring_trails'].append({
                                    'trail_name': trail_name,
                                    'trail_arn': trail_arn,
                                    'read_write_type': read_write_type
                                })
                                monitored_buckets[bucket_name_from_arn]['read_write_type'].add(read_write_type)

                    # If S3 data events are enabled globally
                    if is_s3_data_event and not any(fs.get('Field') == 'resources.ARN'
                                                  for fs in selector.get('FieldSelectors', [])):
                        # This means all S3 buckets are being monitored
                        if bucket_name:
                            if bucket_name not in monitored_buckets:
                                monitored_buckets[bucket_name] = {
                                    'monitoring_enabled': True,
                                    'monitoring_trails': [],
                                    'read_write_type': set(),
                                    'selector_type': 'Advanced'
                                }
                        else:
                            # Get list of all buckets
                            s3 = slave_session.client('s3')
                            all_buckets = s3.list_buckets()['Buckets']
                            for bucket in all_buckets:
                                bucket_name = bucket['Name']
                                if bucket_name not in monitored_buckets:
                                    monitored_buckets[bucket_name] = {
                                        'monitoring_enabled': True,
                                        'monitoring_trails': [],
                                        'read_write_type': set(),
                                        'selector_type': 'Advanced'
                                    }

                        # Add trail information
                        for bucket in monitored_buckets:
                            monitored_buckets[bucket]['monitoring_trails'].append({
                                'trail_name': trail_name,
                                'trail_arn': trail_arn,
                                'read_write_type': read_write_type
                            })
                            monitored_buckets[bucket]['read_write_type'].add(read_write_type)

            except Exception as e:
                print(f"Error processing trail {trail_name}: {str(e)}")
                continue

        # Convert set to list for JSON serialization
        for bucket in monitored_buckets:
            monitored_buckets[bucket]['read_write_type'] = list(monitored_buckets[bucket]['read_write_type'])

        return monitored_buckets

    except Exception as e:
        print(f"Error checking S3 object monitoring: {str(e)}")
        return {}

def export_s3_monitoring_to_csv(monitoring_data, output_file='s3__data_event_monitoring.csv'):
    """Export S3 monitoring information to CSV"""
    headers = [
        'account',
        'bucket_name',
        'monitoring_enabled',
        'selector_type',
        'read_write_types',
        'monitoring_trails'
    ]

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()

        for account, buckets in monitoring_data.items():
            for bucket_name, details in buckets.items():
                row = {
                    'account': account,
                    'bucket_name': bucket_name,
                    'monitoring_enabled': details['monitoring_enabled'],
                    'selector_type': details['selector_type'],
                    'read_write_types': ', '.join(details['read_write_type']),
                    'monitoring_trails': ', '.join([f"{trail['trail_name']} ({trail['read_write_type']})"
                                                  for trail in details['monitoring_trails']])
                }
                writer.writerow(row)

    print(f"CSV file '{output_file}' has been created")







if __name__ == '__main__':

    master_role_arn = f"arn:aws:iam::038462757316:role/cia_master_management_terraform_role-v2"
    slave_role_name = "cloud_management_terraform-ec2-role-v2"
    session_name = f"CIA-Terraform-Pipeline-CT"
    slave_account_id = '038462757316'

    result = {}


    master_session = assume_master_role(master_role_arn= master_role_arn, session_name=session_name)
    slave_session = assume_slave_role(slave_account_id=slave_account_id, slave_role_name=slave_role_name, 
                                           session_name=session_name, master_role_arn=master_role_arn, 
                                           master_session=master_session)


    if not slave_session:
        sys.exit(1)
    

    cloudtrail_data = {}
    cloudtrail_data[slave_account_id] = analyze_cloudtrail_costs(slave_session)
    trails_to_csv(cloudtrail_data, output_file='trails.csv')
    
    s3_data = {}
    s3_data[slave_account_id] = analyze_s3_buckets(slave_session)
    s3_to_csv(s3_data, output_file='s3_buckets.csv')

    s3_object_event_data = {}
    s3_object_event_data[slave_account_id] = check_s3_object_monitoring(slave_session)
    export_s3_monitoring_to_csv(s3_object_event_data, output_file='s3_monitoring.csv')
