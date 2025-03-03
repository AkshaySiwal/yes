

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
