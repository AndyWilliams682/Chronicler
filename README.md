# Incursion Reader

A tool that analyzes screenshots from Path of Exile and reads the Incursion menu, which has a temple (made up of 13 rooms). These rooms may or may not be connected. There is also a room that is selected for the specific Incursion event, and the player may change that room to one of two options.

## Tool Showcase
![](https://imgur.com/a/OGFHl2Y.png)
The main features that need to be recognized from this image are:
  1) What rooms are in the temple? Where are they? (Ex: Pits is the third layer up, second from the right)
  2) What rooms are connected? What rooms are "Opened" (have a path to the Entrance)? (Ex: Workshop is not "opened")
  3) How many Incursions are remaining (1 in this image)
  4) What are the two options for the selected room (Pits is the selected room, it can turn into either Lightning Workshop or Jeweller's Workshop)

These features are stored in a Temple object, which is printed below:
```
             (APX)
             /   \
         (CR2) — ($$2)
         /   \   /   \
     (PS2) —*(hh0)*— (UP3)
     /           \   /   \
 (MM1)   [LF1]   (MN1) — (PP2)
     \               \   /
     (GM1)   (ENT) — (TM2)
    1 Incursions Remaining
      LN1 <-- hh0 --> IR1
```

## Future Work
The goal is to eventually create a tool to help players optimally build their temples across the 12 Incursions.
