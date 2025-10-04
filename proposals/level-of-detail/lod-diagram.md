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
                    | Calculate LOD  |
                    |    Metric      |
                    +----------------+
                             |
                             v
                    +----------------+
                    | Compare with   |
                    | LOD Thresholds |
                    +----------------+
                             |
                             v
              +-----------------------------+
              |                             |
              v                             v
    +-----------------+           +-----------------+
    | Select Single   |           | Cross-fade      |
    | LOD Level       |           | Between Levels  |
    +-----------------+           +-----------------+
              |                             |
              +-----------------------------+
                             |
                             v
                    +----------------+
                    |   Render       |
                    |   Scene        |
                    +----------------+
```

## Transition Between LOD Levels

```
  LOD Metric Value
  |
  |                Transition Width
  |                <------------->
  |
  |    LOD 0                      LOD 1
  |    100%                        0%
  |      |\                        /|
  |      | \                      / |
  |      |  \                    /  |
  |      |   \                  /   |
  |      |    \                /    |
  |      |     \              /     |
  |      |      \            /      |
  |      |       \          /       |
  |      |        \        /        |
  |      |         \      /         |
  |    0%|          \____/          |100%
  |                Blend
  |
  +--------------------------------------->
       Threshold
```
