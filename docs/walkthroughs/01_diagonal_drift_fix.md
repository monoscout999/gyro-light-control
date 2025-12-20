Walkthrough - Diagonal Drift Fix (Scalar Yaw Offset)
The Problem
The user reported that the pointer moved "diagonally" when they rotated their body purely left/right (Yaw).

Symptom: "I move Alpha (Yaw), but the pointer goes up/down as if Beta (Pitch) changed."
Observation: Using the "Calibrate" button made it often worse.
Observation: Using "Reset" (clearing calibration) fixed the diagonal drift but left the pointer unaligned (not pointing to center).
Root Cause Analysis
The previous calibration system used a 3D Rotation Matrix to align the phone's current vector to the target vector.

If the user's hand was slightly tilted (Pitch/Roll != 0) when pressing "Calibrate", the system calculated a matrix that "tilted the entire world" to make the pointer match the center.
Effectively, this created a "Twisted Horizon".
Rotating purely horizontally in a "Twisted World" results in diagonal movement relative to the screen.
The Solution: Scalar Yaw Offset
We abandoned the 3D Matrix Calibration in favor of a simpler 1D Scalar Offset.

Logic: Instead of rotating the 3D world, we simply redefine where "North" is.

Calibration: When user press "Calibrate", we record alpha_offset = current_sensor_alpha.
Runtime: corrected_alpha = real_alpha - alpha_offset.
Beta/Gamma: Touched 0%. They pass through raw.
Why this works:

Since Beta (Pitch) is never modified, the horizon stays perfectly flat (Z=0 never changes to Z!=0).
The user can align the pointer to the wall center (heading) without risking "tilting" the physics.
Modified Files

server_fixed.py
Replaced calibration_matrix (numpy array) with alpha_offset (float).
Removed calls to 

create_calibration_offset
 and 

apply_calibration
.
Implemented simple subtraction logic in 

process_sensor_data
.

mobile.html
Simplified UI to a single "CALIBRAR (CENTRAR)" button.
Removed failed attempts at "Auto-Calibration" and "Reset/Red" buttons.