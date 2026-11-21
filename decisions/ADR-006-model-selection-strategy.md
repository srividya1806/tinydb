# ADR-006: Model Selection Strategy across SDLC Roles

## Status
Accepted

## Context
Different SDLC stages present disparate reasoning requirements:
- Requirements and Design require structured reasoning, prompt instruction following, and architectural synthesis.
- Implementation and Test authoring require high coding proficiency, strict syntax compliance, and fast generation speeds.
- Review requires deep critical analysis, edge-case anticipation, and resistance to superficial pattern-matching.

We must select models that optimize the trade-off between ability, latency, and API cost, while adhering to the user's selected Gemini API platform.

Options considered:
1. **Uniform Single Model (Gemini 2.5 Pro for All Stages)**: High quality across the board, but slow execution speeds and high token cost ($1.25 / 1M input tokens). A multi-stage backtrack run easily consumes 300k+ tokens.
2. **Uniform Single Model (Gemini 2.5 Flash for All Stages)**: Extremely fast (sub-second responses) and very cheap ($0.075 / 1M input tokens), but flash models can suffer from superficial code review (rubber-stamping).
3. **Tiered Hybrid Architecture**: Fast Flash models for operational/code authoring stages, paired with Pro (or specialized adversarial prompt tuning on Flash) for the Independent Reviewer stage.

## Decision
We choose **Google Gemini 3.8 Flash**:
- **Requirements Agent**: `gemini-3.8-flash`. Fast, cost-efficient, and highly capable at extracting structured acceptance criteria.
- **Design Agent**: `gemini-3.8-flash`. Rapidly cross-references `ARCHITECTURE.md` with source symbols.
- **Implementation & Testing Agents**: `gemini-3.8-flash`. High code-completion throughput and near-instant feedback for test-driven refinement loops.
- **Independent Reviewer Agent**: `gemini-3.8-flash` with zero temperature (`temperature=0.0`) and strict adversarial system prompting. This ensures the reviewer evaluates diffs critically without sycophancy.

## Consequences
### Positive
- Cost efficiency: >85% of total pipeline tokens run on the highly cost-effective Flash tier, keeping total run cost below $0.05 per issue.
- Latency optimization: Implementation and testing loops finish in seconds rather than minutes.
- Cognitive diversity: Using distinct models or distinct prompt topologies between implementer and reviewer reduces correlated errors.

### Negative
- Requires maintaining dual model configurations in the workflow environment.
