# Measurements

One file per test, so that every number used in a decision can be traced to how it was measured.
Name files `YYYY-MM-DD-short-title.md`, for example `2026-12-02-load-test-3-cameras.md`.

Each file contains:

1. **Goal**: what question the test answers, and the requirement ID.
2. **Setup**: which computer, which cameras, power mode, Git commit or tag, settings.
3. **Procedure**: the exact commands, so someone else can repeat the test.
4. **Results**: the raw numbers (tables, plots). Large raw files go to shared storage; link them here.
5. **Conclusion**: what we learned and what we decided (link the decision record).

| Date | Test | Requirement |
|---|---|---|
| 2026-11-25 | [**Summary of all camera tests that day**](2026-11-25-camera-tests-summary.md) | REQ-AUT-ISS-06, REQ-AUT-020, REQ-AUT-120 |
| 2026-11-25 | [Camera load test, 1 to 3 ZED 2i on the bench Jetson](2026-11-25-zed-load-test-3-cameras.md) | REQ-AUT-ISS-06 |
| 2026-11-25 | [Depth modes compared on a lab recording](2026-11-25-depth-modes-lab.md) | REQ-AUT-020, REQ-AUT-120 |
