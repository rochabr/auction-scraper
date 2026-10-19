# Valuation and recommendation policy

Implement config/valuation-policy.yaml in pure Decimal functions in src/auction_assistant/valuation.py. These are initial product rules to calibrate and qualify; never represent them as measured accuracy or provider facts.

## Eligibility and confidence

Use independently realized transactions, not asking prices or estimates. Verify artist identity, attribution and medium through recorded evidence. Dimensions are source-recorded width/height in the same unit: abs(sale_dimension / subject_dimension - 1) must be <=0.20 for each; dimensions must be positive. Do not rotate or rescale dimensions to improve a match.
Apply the ten-year lookback as of the frozen analysis timestamp. When both artwork dates exist, their difference must be <=10 years. Unknown dates or condition are explicit evidence gaps, require no adjustment and cap confidence at low. Known incompatible condition is excluded. Unknown artist, attribution, medium, price basis, dimensions or required FX prevents an eligible comparison.
Deduplicate provider IDs and cross-source identity (artist, artwork, sale event/date, lot and realized amount); retain the independent-transaction identifier and exclusion reason. Re-sales are distinct transactions but the same artwork may not cross calibration/holdout boundaries.
Compute median/IQR exactly as AGENTS.md specifies. Relative dispersion is (Q3-Q1)/median for a positive median. Confidence uses the highest fully satisfied tier; all matching attributes must be supported and current enough for medium/high. Confidence is an evidence grade, not a probability of investment return.

## Candidate price, labels and ranking

A candidate hammer is the documented next legal bid for an active lot, or the starting hammer before bids begin. If neither is available, still show a supported valuation and computed maximum bid when the ladder/fees support it, but do not invent a current-price label or ranking ratio.
Compute candidate total with the same T(h), currency and costs as the bid cap. Nonpositive or unconvertible candidate totals cannot enter ranking.
Apply label precedence:
1. insufficient_evidence: valuation unsupported or candidate/cost inputs required for a label missing. Explain separately whether valuation or maximum bid can still be displayed.
2. avoid: no positive legal bid fits the acquisition cap, or candidate total >= upper valuation bound.
3. opportunity: candidate total <= acquisition cap and confidence medium/high.
4. watch: all other supported cases.
A user budget affects affordability and labels, not the market valuation. Unknown authenticity/physical condition remains a visible risk; historical significance never changes numeric results.
Rank by the exact ordered keys in config/valuation-policy.yaml; ratio is V_low / candidate total, with no hidden weighted score. Use stable normalized lot IDs for final ties and retain inputs.

## Required fixtures and calibration gates

Extend tests/unit/test_valuation.py and test_bid_limits.py with minimum-sample, duplicate, 20% dimension/10-year date boundaries, unknown data, confidence tier edges, dispersion and label precedence.
Test candidate total equal to cap (eligible opportunity with sufficient confidence), equal to upper bound (avoid), budget below every legal bid (avoid) and absent candidate (insufficient evidence for label; supported valuation may remain).
Test each ranking key independently and stable ties. Never use LLM text to assign labels.
Freeze >=30 independent calibration and >=30 independent held-out sale outcomes split by time and artwork identity. Exclude a target sale from its own comparable sample. Select supported error/coverage thresholds from calibration, review/freeze them and the dataset hashes before evaluating the holdout; missing thresholds/data or unmet thresholds fail.
For valuation-error evaluation use the eligible evidence before the target sale date and normalize target/prediction to the same currency/price basis. Report excluded cases, coverage denominator, sample size, median absolute percentage error and 25th-75th range coverage.
