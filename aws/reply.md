### Email Draft: Update on AWS Resource Tagging Task

Subject: Update on AWS Resource Tagging and SCP Implementation

Dear [Manager's Name],

I've made significant progress on addressing the untagged AWS resources and implementing preventative measures as requested. Here's a comprehensive update:

**Amazon Rekognition (null_623964595746 and null_477928018413)**
* The untagged costs are from Rekognition's DetectModerationLabels API calls consumed by the `boltx-mkt_catalog_job-w0mkzkx3` role
* These are serverless API calls without directly associated resources, making them impossible to tag through standard methods
* Recommendation: Consider migrating these workloads to a dedicated account for clearer cost segregation and visibility

**Amazon SageMaker (null_623964595746 and null_477928018413)**
* "APN2-Host" usage types: These SageMaker Endpoints were tagged to the `reach_sagemaker` role as of February 18th and 20th (screenshots provided separately)
* "APN2-Studio:KernelGateway" and "APN2-Studio:VolumeUsage" types: These remain untagged because the SageMaker domains lack "Custom tag propagation" enabled
* Required solution: We need to enable "Custom tag propagation" on all domains. Once implemented:
  - Existing resources will require restart to inherit tags
  - New resources will automatically inherit tags going forward

**SCP Policy Implementation**
I'm developing a Service Control Policy with conditional checks to enforce "Custom tag propagation" when creating or updating SageMaker domains. This preventative measure will ensure all future SageMaker resources inherit proper tags, eliminating the root cause of untagged resources.

The policy implementation is in final testing and should be ready for review by [specific date/time].

Please let me know if you'd like me to prioritize any specific aspect of this work or if you need additional information.

Best regards,
[Your Name]
