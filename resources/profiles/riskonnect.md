# Riskonnect adaptation profile

Authority: current project instructions and architectural/evidence contracts,
development guide, actual prompt/schema/replay surfaces and tracker metadata.
Source identities/versions are in provenance; these references grant no access.
Coding-agent work must not access Databricks under this profile.

Map actual editable prompt packs/wire hints/validated replay and consumers before
editing. Preserve source authority, uncertainty, redaction, application-owned
timestamp/identity fields and accepted-output-only replay; do not invent layers
or universalize historical cleanroom assumptions.

Application-owned fields are added and validated by the application. Keep their
ownership out of model-facing generation hints/examples according to the actual
mapped contract, while preserving final validated output and replay consumers.
Historical source field names, journal widths and cleanroom assumptions are not
defaults for transfer projects.

For this reference contract only, report evidence timestamps come from `CreatedDate`
and clinical-note evidence timestamps from `ServiceInstant`. Neither automatically
means the clinical event's occurrence time. Do not substitute an event date or a
note creation timestamp. The application supplies evidence identities and times;
failed JSON, validation errors and repair instructions never enter accepted replay.
Model-visible changes update logical prompt identity/version/SHA-256 where the
project's current prompt contract requires them. Map another project's actual
source fields and consumers rather than copying these clinical names.

Map observable BDD outcomes and current local canonical checks explicitly. Tracker
coverage separates primary delivery, enabling work and validation; complete relevant
pagination and preserve actual metadata/priorities. Historical issue keys and
clinical/source table/date settings are not portable defaults. Tracker writes and
model-backed checks require separate applicable permission and read-back/protocol.
