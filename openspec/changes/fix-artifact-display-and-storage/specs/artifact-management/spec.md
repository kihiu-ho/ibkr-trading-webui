## MODIFIED Requirements
### Requirement: Artifact Storage and Display
The system SHALL properly store and display artifacts with all data fields, including charts stored in MinIO.

#### Scenario: Artifact endpoint returns complete data
- **WHEN** user requests artifact by ID via `/api/artifacts/{id}`
- **THEN** return complete artifact data with all fields
- **AND** handle Decimal types by converting to float for JSON serialization
- **AND** return proper JSON response (not empty)

#### Scenario: Chart artifacts with MinIO URLs
- **WHEN** chart is generated in workflow
- **THEN** upload chart PNG to MinIO
- **AND** store MinIO URL in artifact image_path field
- **AND** display chart image from MinIO URL in artifacts page
- **AND** charts remain accessible after container restart

#### Scenario: Decimal JSON serialization
- **WHEN** artifact contains Decimal values (e.g., confidence scores)
- **THEN** convert Decimal to float before JSON serialization
- **AND** store artifact successfully without serialization errors
- **AND** return Decimal values as float in API responses

## ADDED Requirements
### Requirement: Chart MinIO Upload
The system SHALL upload chart images to MinIO before storing as artifacts.

#### Scenario: Upload chart to MinIO
- **WHEN** chart is generated in workflow
- **THEN** upload chart PNG file to MinIO
- **AND** generate MinIO public URL
- **AND** store MinIO URL in artifact image_path
- **AND** fallback to local path if MinIO upload fails

