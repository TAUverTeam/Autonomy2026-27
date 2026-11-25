# 0001. Start a new code base instead of continuing last season's

- **Status:** Accepted
- **Date:** 2026-11-18
- **Decided by:** Autonomy team leader, 2026/27
- **Requirements:** REQ-AUT-ISS-04, REQ-AUT-170

## Problem

The 2026/27 Autonomy team is entirely new. Last season's code
([TAUverIL/Exodus_Autonomy](https://github.com/TAUverIL/Exodus_Autonomy), branch `testing`, commit
`53454f0`) reached a working demo on a camera test cart, but nobody who wrote it is still on the team.
We had to decide whether to build on that code or start over.

## Options considered

1. **Continue the old repository.** Pros: a working pipeline exists (cameras → obstacle map → path
   planner → driving command), tested in experiments in July–August 2026. Cons: see below.
2. **Start a new repository and use the old one as reference.** Pros: a clean structure we understand
   and document from the first line. Cons: we must rebuild what already worked, which costs time.

## Decision

Start a new, Autonomy-only repository. Last season's code, reports and recordings are used as a source
of knowledge (what worked, what failed, what settings were measured), not as code to copy.

## Why

- **Nobody on the team understands the old code**, and much of it is not documented. Building on code
  we cannot explain is risky on a robot.
- **The old repository mixes several teams** (autonomy, arm, motors, telecom, CAN) with copies of
  third-party drivers, and it contains build output (`build/`, `install/`, `log/`). REQ-AUT-ISS-04 asks
  for one clean, documented Autonomy code base that a new member can build.
- **It was set up for the test cart, not the rover** (REQ-AUT-ISS-10): rover size, camera positions
  and only one of three cameras feeding the obstacle map.
- **Several parts were stand-ins**: the rover mode was faked, position came only from the front camera
  through a manual relay, and the driving command does not match what C&C's drive software listens
  to (REQ-AUT-ISS-07). These need redesigning together with C&C anyway.
- The project head asked that new code start only after the three diagrams are drawn from scratch
  (REQ-AUT-ISS-01/02/03). A fresh code base follows those diagrams directly.

## Consequences

- We lose time rebuilding parts that worked. To limit this, [previous-season.md](../previous-season.md)
  records what worked and the settings they measured, so we do not repeat their experiments blindly.
- Copying a small piece of old code is allowed **only** if the person copying it understands it fully,
  documents it to our standard, and notes the origin in the file header.
- The old repository stays read-only as an archive. We do not delete it; other teams may still use it.
