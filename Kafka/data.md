

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
  
