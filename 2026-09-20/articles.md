# Further Reading: How to Measure What One AI Task Costs in Dollars and Watts

## Articles

### 1. [Measuring the environmental impact of AI inference](https://cloud.google.com/blog/products/infrastructure/measuring-the-environmental-impact-of-ai-inference)
**Source**: Google Cloud | **Date**: 2025-08-21 | **Read time**: ~10 min
> The primary source for this session, and the only place a vendor publishes the same prompt measured two ways: 0.10 watt-hours counting the accelerator alone, 0.24 once idle capacity, host processor and memory, and cooling are inside the line. Read this first. It is what lets you argue about a boundary without arguing about a company.

### 2. [Scaling AI with 8 to 20x energy efficiency](https://www.microsoft.com/en-us/microsoft-cloud/blog/2026/06/15/scaling-ai-with-8-to-20x-energy-efficiency/)
**Source**: Microsoft Cloud Blog | **Date**: 2026-06-15 | **Read time**: ~8 min
> Microsoft's summary of its own peer-reviewed measurement: 0.16 to 0.60 watt-hours per typical query, with a median near 0.31. Read it for the four factors they name as driving the variation, three of which you control. Read it skeptically too, and the article says why: "public figures are overstated" is the most convenient possible finding for a company selling inference.

### 3. [Energy use of AI inference, efficiency pathways, and test-time scaling](https://www.cell.com/joule/fulltext/S2542-4351(26)00114-5)
**Source**: Joule (Oviedo et al.) | **Date**: 2026 | **Read time**: ~30 min
> The peer-reviewed paper behind the figure above, and the reason that figure carries more weight than a blog post. Worth the time if you are the person who has to defend an energy number in a room with a sustainability team. The methodology section is the part to read; the headline is already in the link above.

## Papers

### [TokenPowerBench: Benchmarking the Power Consumption of LLM Inference](https://arxiv.org/abs/2512.03024)
**Authors**: see the paper | **Published**: 2025-12
> The one you can open in an editor. A declarative config picks the model, prompt set and inference engine; the measurement layer captures power without special equipment; the metrics pipeline attributes energy separately to the prefill and decode stages. Use it to see how batch size, context length, parallelism and quantization each move joules per token on your own hardware.

### [Where Do the Joules Go? Diagnosing Inference Energy Consumption](https://arxiv.org/pdf/2601.22076)
**Published**: 2026-01
> Read this when your own measurements disagree and you need to know which layer is responsible. It is the diagnostic companion to the benchmark above: less useful for producing a headline number, more useful for explaining one.
