# Level of Detail Diagram

```
  Distance from Camera
  |
  |   LOD 0        LOD 1        LOD 2        LOD 3
  |  (Highest)    (Medium)      (Low)      (Lowest)
  |
  |  +--------+   +--------+   +--------+   +--------+
  |  |        |   |        |   |        |   |        |
  |  | 10,000 |   |  2,000 |   |   500  |   |   100  |
  |  | polys  |   | polys  |   | polys  |   | polys  |
  |  |        |   |        |   |        |   |        |
  |  +--------+   +--------+   +--------+   +--------+
  |
  |<----------|------------|------------|------------->
  |     0-10m      10-50m     50-200m      >200m

```

## LOD Selection Process

```
                          +----------------+
                          |  Camera View   |
                          +----------------+
                                   |
                                   v
                          +----------------+
                          | Check for LOD  | Yes
                          |   Override     |------+
                          +----------------+      |
                                   | No           |
                                   v              |
                 None     +----------------+      |
              appropriate |    Select      |      |
             +------------|   Heuristic    |      |
             |            +----------------+      |
             |                     | Yes          |
             v                     v              |
     +----------------+   +----------------+      |
     |  Use Default   |   |  Compute LOD   |      |
     |     Index      |   |     Index      |      |
     +----------------+   +----------------+      |
             |                     |              |
             |                     v              |
             |            +----------------+      |
             |            |  Select Index  |      |
             |            |  or Cross-Fade |      |
             |            +----------------+      |
             |                     |              |
             |                     v              |
             +-------------------->+<-------------+
                                   v
                          +----------------+
                          |     Render     |
                          |     Scene      |
                          +----------------+
```

## Transition Between LOD Levels

```
  Opacity
  ^
  |              Transition Width
  |                <--------->
  |
  |    LOD 0                      LOD 1
  |    100%                      100%
  |      __________           _______
  |                \  Blend  /
  |                 \       /
  |                  \     /
  |                   \   /
  |                    \ /
  |                     X
  |                    / \
  |                   /   \
  |                  /     \
  |                 /       \
  |    0%__________/         \_______ 0%
  |
  +---------------------------------------> Metric Value
                   ^         ^
         Threshold |         | Blend threshold
```
