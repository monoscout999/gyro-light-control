# Implementation Plan - Fixture Removal and UI Enhancement

The goal is to simplify the application by removing all "moving light fixture" logic and focusing on the 3D visualization of the gyro data within the venue. Additionally, the UI will be overhauled for a more premium, modern look using glassmorphism and optimized layouts.

## User Review Required
> [!IMPORTANT]
> This change will permanently remove the "fixtures" (moving lights) functionality. The app will focus exclusively on visualizing the pointer and sensor data in the 3D venue.

## Proposed Changes

### Backend

#### [DELETE] fixture_manager.py
This module is no longer needed.

#### [MODIFY] server.py
- Remove FixtureManager and Fixture imports.
- Remove app_state.fixtures initialization.
- Remove all /api/fixtures REST endpoints.
- Update process_sensor_data to stop trying to update fixtures.
- Remove fixtures from the get_status response.
- Clean up the main block (remove example fixture creation).

### Frontend

#### [MODIFY] scene3d.js
- Remove FIXTURE and LIGHT_BEAM colors.
- Remove fixtures map from this.objects.
- Delete createFixture, updateFixture, updateFixtures, and removeFixture methods.
- Update onCanvasClick and selectObject to no longer handle fixture selection.

#### [MODIFY] main.js
- Remove fixture-related API calls in handleConnected.
- Remove scene3d.updateFixtures calls in handleStateUpdate.
- Update updatePropertiesPanel to remove fixture-specific logic.

#### [MODIFY] index.html
UI Redesign:
- Implement a "Glassmorphism" theme for all panels.
- Move "Sensor Data" and "Debug Info" to floating or sidebar panels with better styling.
- Improve sliders appearance.
- Replace the "Properties" panel with a more general "Settings/Venue" panel.
- Use a more modern font (already using Inter, will refine usage).

## Verification Plan

### Manual Verification
1. Start the server: `python server.py`.
2. Verify terminal output shows no fixture-related logs.
3. Open index.html in a browser.
4. Scan QR code with mobile or navigate manually to mobile.html.
5. Verify that moving the phone updates the 3D pointer in the visualizer.
6. Verify that no errors appear in the browser console related to missing fixtures.
7. Inspect the new UI for aesthetics and responsiveness.
8. Click on venue or user in 3D to verify property panels still work for those objects.
