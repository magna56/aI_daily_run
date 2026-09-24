# Further Reading: How Much of Your Work a 15B Model Can Actually Close

## Papers

### [Phi-4-reasoning-vision-15B Technical Report](https://arxiv.org/abs/2603.03975)
**Authors**: Aneja, Harrison, Joshi, LaBonte, Langford, Salinas (Microsoft Research) | **Published**: 2026-03-04
> The primary source, and worth reading for the ablation tables rather than the headline. Two rows carry this session: the resolution comparison, where dynamic resolution at 2,048 tokens beats multi-crop given 3,096, and the ScreenSpot-Pro column, where every configuration lands in single digits. Read those before you read the abstract's efficiency claim, so the claim arrives with its limits attached. The arXiv version is the fetchable one; the Microsoft-hosted PDF is 13 MB.

## Articles

### [Phi-4-reasoning-vision and the lessons of training a multimodal reasoning model](https://www.microsoft.com/en-us/research/blog/phi-4-reasoning-vision-and-the-lessons-of-training-a-multimodal-reasoning-model/)
**Source**: Microsoft Research | **Date**: March 2026 | **Read time**: ~10 min
> The authors' own summary, and the faster route to the design decisions if you are not going to read forty pages. Read it for why they chose mid-fusion over early fusion — the reasoning is about compute and data budget rather than quality, which is the honest version of a tradeoff that usually gets framed as an architecture preference.

### [microsoft/Phi-4-reasoning-vision-15B](https://huggingface.co/microsoft/Phi-4-reasoning-vision-15B)
**Source**: Hugging Face | **Date**: March 2026 | **Read time**: ~5 min
> The one you can open in an editor. Open weights, 15B parameters, 16,384 context, images up to 3,600 visual tokens. Read the model card's intended-use section before you plan anything around it, and treat the benchmark table there the way the session treats every averaged score — as a number over a mixed population rather than a statement about your traffic.

### [Introducing Phi-4-Reasoning-Vision to Microsoft Foundry](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/introducing-phi-4-reasoning-vision-to-microsoft-foundry/4499154)
**Source**: Microsoft Community Hub | **Date**: March 2026 | **Read time**: ~4 min
> Skip unless you are deploying it on Azure today, in which case this is the deployment path rather than the research. Included for completeness: it is a product post, and the numbers in it are the report's numbers with the caveats removed.
