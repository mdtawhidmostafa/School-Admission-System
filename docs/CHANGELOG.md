# Focused maintainability cleanup

- Extracted hold-confirm/cancel transition into one focused backend service, preserving the row-lock and status-transition SQL.
- Extracted administrator key checking into a dedicated security helper; credentials stay in memory only.
- Extracted frontend independent polling and last-good data handling into `useAdmissionData`.
- Consolidated localStorage draft persistence in `useSavedField`, avoiding repeated effects.
- Reformatted frontend class/admin form components and removed unused React default imports.
- Added a guard for zero seat count in class progress calculation.
- Updated structural tests to follow moved responsibilities; never treat static tests as runtime validation.
- Did not modify API contracts, underlying database schema, rate limits, or Docker services.

## Remaining release blockers

- Authentic npm lockfiles could not be generated because npm registry requests fail in this environment.
- .NET compiler and Docker are not installed here: the backend clean build and PostgreSQL admission tests are unverified.
- Cross-platform E2E, backup/restore and load benchmark remain outstanding.
