# Fix External Placeholder Image Dependency

## Why
The charts page currently uses an external placeholder service (`via.placeholder.com`) as a fallback when chart images fail to load. This external dependency is failing with `ERR_NAME_NOT_RESOLVED`, causing error messages in the browser console and poor user experience when charts fail to load.

External dependencies for basic UI elements create unnecessary failure points and network requirements. A self-contained solution improves reliability and reduces external network calls.

## What Changes
- Replace external `via.placeholder.com` dependency with a local SVG-based placeholder
- Use inline SVG data URI that requires no external network calls
- Maintain the same visual feedback when charts fail to load
- Eliminate `ERR_NAME_NOT_RESOLVED` errors from browser console

## Impact
- **Affected specs:** chart-visualization
- **Affected code:** 
  - `frontend/templates/charts.html` (image error handler)
- **User impact:** More reliable placeholder display when charts fail to load, no external network dependency
- **Breaking changes:** None - purely improves existing error handling

