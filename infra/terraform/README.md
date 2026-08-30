# MarketPulse Terraform infrastructure

This configuration manages the existing Google Cloud infrastructure used by
MarketPulse.

## Managed resources

- Cloud Storage bucket for immutable raw API payloads
- BigQuery dataset for curated and analytical data
- Partitioned and clustered `daily_prices` BigQuery table

The resources were initially created outside Terraform and adopted through
Terraform import. A clean plan after import confirmed that the configuration
matches the live infrastructure.

## Safety controls

- `prevent_destroy` protects the bucket, dataset, and table from accidental
  destruction through Terraform.
- The raw bucket has `force_destroy = false`.
- The BigQuery table has deletion protection enabled.
- Public access prevention and uniform bucket-level access are enforced on the
  raw bucket.

These controls protect Terraform operations but do not prevent authorized
changes made directly through Google Cloud.

## Prerequisites

- Terraform 1.15 or later
- Google Cloud Application Default Credentials
- Access to the target Google Cloud project

Authenticate locally when needed:

```powershell
gcloud auth application-default login
```

## Local setup

Create the ignored local variable file:

```powershell
Copy-Item terraform.tfvars.example terraform.tfvars
```

Replace the placeholder project and bucket identifiers, then initialize and
validate the configuration:

```powershell
terraform init
terraform fmt -check -recursive .
terraform validate
```

## Importing existing resources

Import the resources before the first plan in a new Terraform state:

```powershell
terraform import google_storage_bucket.raw "<raw-bucket-name>"
terraform import google_bigquery_dataset.analytics "projects/<project-id>/datasets/<dataset-id>"
terraform import google_bigquery_table.daily_prices "projects/<project-id>/datasets/<dataset-id>/tables/<table-id>"
```

Then confirm that the imported infrastructure matches the configuration:

```powershell
terraform plan
```

Review every proposed action before applying. The expected plan immediately
after a correct import is `No changes`.

## State

Terraform state and real variable files are excluded from version control.
Never commit `.tfstate` or `terraform.tfvars` files. The current bootstrap uses
local state; a dedicated remote backend should be configured before shared or
automated Terraform operations.
