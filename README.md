# Tesseract Foundry

AI inference platform built by Foundry AI. A modular, high-performance inference solution for deploying, managing, and scaling AI models in production.

## Philosophy

Tesseract Foundry treats inference as a first-class product — not a side effect of training. Every component is designed for production-grade serving, monitoring, and iteration.

## Versions

| Version | Focus |
|---------|-------|
| v1 | Foundation — project skeleton, config, logging |
| v2 | Core Engine — model loading, pipeline, batching |
| v3 | API Layer — REST & gRPC endpoints, auth |
| v4 | Model Management — registry, versioning, A/B testing |
| v5 | Production — monitoring, auto-scaling, CI/CD, Docker |

## Quick Start

`ash
pip install -e .
tesseract-foundry serve --config config.yaml
`

## License

MIT
