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
                        status = slave_cloudtrail.get_trail_status(Name=trail['trail_arn'])
                        trail_status = status.get('IsLogging', 'Error')
                    except Exception as e:
                        print(f"ERROR: Unable to get trail status for {trail['trail_name']}: {str(e)}")
                        trail_status = 'Error'
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
    fields = fields - {'trail_name', 'trail_status', 'trail_s3_bucket', 'has_data_events', 'data_events_read_write', 'has_management_events', 'management_events_read_write', 'has_insight_selector', 'is_multi_region', 'is_organization_trail'}

    # Define column order with unique columns
    base_columns = ['account', 'trail_name', 'trail_status', 'region', 'trail_s3_bucket', 'has_data_events', 'data_events_read_write', 'has_management_events', 'management_events_read_write', 'has_insight_selector', 'is_multi_region', 'is_organization_trail']
    remaining_columns = sorted(list(fields))

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
    result[slave_account_id] = analyze_cloudtrail_costs(slave_session)
    trails_to_csv(result)
