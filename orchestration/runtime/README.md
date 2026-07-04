# Runtime Integration

This module bridges Chameha and the Cognitive Runtime.

Responsibilities

- model selection
- provider selection
- runtime capability lookup
- inference execution
- accelerator selection
- model lifecycle

The orchestration layer never performs inference directly.

It delegates inference to the Cognitive Runtime.
