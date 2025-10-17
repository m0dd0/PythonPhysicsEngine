# Architecture
As outlined in the README, this physics engine is built with modularity and extensibility in mind.
Since performance is extremly poor anyways due to the use of pure Python, the focus is on clean architecture and easy experimentation rather than raw speed.
To achieve a high degree of modularity, the engine is built around several key abstract strategies that can be swapped out easily.
This allows users to experiment with different algorithms and implementations without modifying the core engine code.

Heres an overview of the most important classes used in the engine:
TODO: insert class diagram here