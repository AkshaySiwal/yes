

https://developer.hashicorp.com/terraform/enterprise/api-docs/notification-configurations#run-notification-payload

## Apply
```
{
  "payload_version": 1,
  "notification_configuration_id": "nc-mBVYHzTMXaRA5ueC",
  "run_url": "https://app.terraform.io/app/your-org/workspaces/example-workspace/runs/run-CZcmD7eagjhyX0vN",
  "run_id": "run-CZcmD7eagjhyX0vN",
  "run_message": "Triggered by a merge to main branch",
  "run_created_at": "2023-04-20T15:48:29.272Z",
  "run_created_by": "user@example.com",
  "workspace_id": "ws-D6fJsasdGj3E9eFN",
  "workspace_name": "example-workspace",
  "organization_name": "your-org",
  "notifications": [
    {
      "message": "Run completed successfully",
      "trigger": "run:completed",
      "run_status": "applied",
      "run_updated_at": "2023-04-20T15:52:47.584Z",
      "run_updated_by": "user@example.com"
    }
  ]
}
```


## Apply Error

```
{
  "payload_version": 1,
  "notification_configuration_id": "nc-mBVYHzTMXaRA5ueC",
  "run_url": "https://app.terraform.io/app/your-org/workspaces/example-workspace/runs/run-CZcmD7eagjhyX0vN",
  "run_id": "run-CZcmD7eagjhyX0vN",
  "run_message": "Triggered by a merge to main branch",
  "run_created_at": "2023-04-20T15:48:29.272Z",
  "run_created_by": "user@example.com",
  "workspace_id": "ws-D6fJsasdGj3E9eFN",
  "workspace_name": "example-workspace",
  "organization_name": "your-org",
  "notifications": [
    {
      "message": "Run errored",
      "trigger": "run:errored",
      "run_status": "errored",  // or "canceled" if it was canceled
      "run_updated_at": "2023-04-20T15:52:47.584Z",
      "run_updated_by": "user@example.com",
      "error_message": "Error applying plan: Error creating resource: [error details]"  // Only present for errored runs
    }
  ]
}
```

### What is HMAC?
HMAC (Hash-based Message Authentication Code) is a specific type of message authentication code that combines a cryptographic hash function with a secret key to verify both the data integrity and authenticity of a message.


Implement HMAC Verification in Your API:
```

import hmac
import hashlib

def verify_tfe_signature(request_body, signature_header, shared_secret):
    computed_signature = hmac.new(
        shared_secret.encode('utf-8'),
        request_body.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(computed_signature, signature_header)
```
Configure Your API to Extract the Signature:
- Look for the x-tfe-notification-signature header in incoming requests
- Use the same token you configured in TFE to verify the signature
- Reject requests with invalid signatures

```
from flask import Flask, request, jsonify
import hmac
import hashlib
import json

app = Flask(__name__)
TFE_SHARED_SECRET = "your-secret-token"  # Same token configured in TFE

@app.route('/add_event', methods=['POST'])
def add_event():
    # Get the signature from the header
    signature = request.headers.get('x-tfe-notification-signature')
    if not signature:
        return jsonify({"error": "Missing signature header"}), 401

    # Get the request body as a string
    request_body = request.get_data(as_text=True)

    # Verify the signature
    computed_signature = hmac.new(
        TFE_SHARED_SECRET.encode('utf-8'),
        request_body.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()

    if not hmac.compare_digest(computed_signature, signature):
        return jsonify({"error": "Invalid signature"}), 401

    # Process the webhook payload
    payload = request.json

    # Extract information from the payload
    run_status = payload.get('notifications', [{}])[0].get('run_status')
    workspace_name = payload.get('workspace_name')

    # Your business logic here
    # ...

    return jsonify({"message": "Event created successfully"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```




```
def get_workspace_project(tfe_hostname, tfe_token, workspace_id):
    headers = {
        'Authorization': f'Bearer {tfe_token}',
        'Content-Type': 'application/vnd.api+json'
    }
    url = f"https://{tfe_hostname}/api/v2/workspaces/{workspace_id}"
    logger.info(f"Getting workspace details for workspace id: {workspace_id}")

    response = requests.get(url, headers=headers, allow_redirects=True)
    project_name = None

    if response.status_code == 200:
        resp_json = response.json()
        try:
            # Extract project ID first
            project_id = resp_json['data']['relationships']['project']['data']['id']
            logger.info(f"Found project ID: {project_id}")

            # Make another API call to get project details
            project_url = f"https://{tfe_hostname}/api/v2/projects/{project_id}"
            project_response = requests.get(project_url, headers=headers)

            if project_response.status_code == 200:
                project_json = project_response.json()
                project_name = project_json['data']['attributes']['name']
                logger.info(f"Workspace belongs to project: {project_name}")
        except KeyError:
            logger.error("Failed to extract project information from workspace data")
            pass

    return project_name
```


```
def extract_aws_account_from_project(project_name):
    if project_name is None:
        logger.warning("Project name is None, cannot extract AWS account number")
        return None

    logger.info(f"Checking if project name '{project_name}' contains AWS account number")

    # AWS account numbers are 12 digits
    aws_account_pattern = re.compile(r'\b\d{12}\b')
    match = aws_account_pattern.search(project_name)

    if match:
        aws_account = match.group(0)
        logger.info(f"Found AWS account number: {aws_account}")
        return aws_account
    else:
        logger.info(f"No AWS account number found in project name")
        return project_name
```
