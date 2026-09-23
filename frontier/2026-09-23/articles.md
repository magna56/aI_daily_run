# Further Reading: How 1,024 Agents Split One Task Without a Coordinator

## Papers

### [Agensh: Scaling Organizational Intelligence to 1,024 Agents](https://arxiv.org/abs/2609.26781)
**Source**: Microsoft Research | **Published**: 2026-09-23 | **Read time**: ~40 min
> The primary source. Read the method section for the three pieces of shared state — workspace, message interface, shared context — because that decomposition is the part you would actually copy. Then read the results with the question this session is built on in hand: the scaling curve varies agent count without normalizing token spend, so decide for yourself which of the two the numbers are measuring before you quote them.

### [RRSI: Regularized Recursive Self-Improvement of Agent Harnesses](https://arxiv.org/abs/2609.24972)
**Source**: Google Research | **Published**: September 2026 | **Read time**: ~40 min
> The companion piece, and worth reading in the same sitting. Agensh scales a harness sideways by adding workers; RRSI improves one harness by evolving it. Both are automating the thing around the model rather than the model, and both show how easily a gain in a controlled setting fails to transfer. Read it if you want the other half of the picture.

## Articles

### [The Organizational Behavior of Agentic AI: Collective Intelligence in Human-Agent Workflows](https://arxiv.org/pdf/2606.30986)
**Published**: 2026-06 | **Read time**: ~30 min
> Background, for the framing rather than the method. Useful if the phrase "organizational intelligence" sounded like marketing to you — it is a real line of work with its own vocabulary, and this is the clearest map of it. Skip if you only want the claim protocol.
