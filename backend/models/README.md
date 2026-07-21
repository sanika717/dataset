Model weight files (`ppe.pt`, `hook_load.pt`, `bytetrack.yaml`) are not
included in this project — they're your trained weights, and weren't
part of any uploaded phase. Drop them in here:

    models/ppe.pt
    models/hook_load.pt
    models/bytetrack.yaml

PPEDetector (backend/detector/ppe_detector.py) falls back to a generic
`yolov8n.pt` (downloaded automatically by ultralytics on first use) if
`models/ppe.pt` is missing or empty, so the app will still run without
it — it just won't detect PPE violations, only generic "person" boxes.
HookLoadDetector has no such fallback and will raise on first use if
`models/hook_load.pt` isn't present.
