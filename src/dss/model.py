"""Explainable min-max MCDA ranking used by the London road safety DSS."""
from __future__ import annotations
from dataclasses import dataclass, field
from math import isfinite, isclose

@dataclass(frozen=True)
class Criterion:
    name: str
    weight: float
    higher_is_better: bool = True

@dataclass(frozen=True)
class Alternative:
    name: str
    scores: dict[str, float]

@dataclass(frozen=True)
class Recommendation:
    chosen: str
    ranking: list[tuple[str, float]]
    reason: str
    contributions: dict[str, dict[str, float]] = field(default_factory=dict)
    tied: tuple[str, ...] = ()
    excluded: tuple[str, ...] = ()

class DecisionSupportModel:
    def __init__(self, criteria: list[Criterion], choice_threshold: float = 0.0):
        if not criteria or len({c.name for c in criteria}) != len(criteria):
            raise ValueError('Criteria must be nonempty and have unique names.')
        if any(not isfinite(c.weight) or c.weight < 0 for c in criteria):
            raise ValueError('Weights must be finite and nonnegative.')
        self.criteria = [c for c in criteria if c.weight > 0]
        self._weight_sum = sum(c.weight for c in self.criteria)
        if not isfinite(self._weight_sum) or self._weight_sum <= 0:
            raise ValueError('At least one weight must be positive.')
        if not isfinite(choice_threshold) or not 0 <= choice_threshold <= 1:
            raise ValueError('Threshold must be between 0 and 1.')
        self.choice_threshold = choice_threshold

    def intelligence(self, alternatives):
        if len({a.name for a in alternatives}) != len(alternatives):
            raise ValueError('Alternative identifiers must be unique.')
        ready = [a for a in alternatives if all(
            c.name in a.scores and isinstance(a.scores[c.name], (int, float))
            and isfinite(a.scores[c.name]) for c in self.criteria)]
        if not ready:
            raise ValueError('No alternatives have complete finite criteria.')
        return ready

    def contributions(self, alternatives):
        result = {a.name: {} for a in alternatives}
        for c in self.criteria:
            values = [a.scores[c.name] for a in alternatives]
            low, high = min(values), max(values)
            for a in alternatives:
                # Constant criteria provide no evidence for prioritizing any alternative.
                value = 0.0 if high == low else (a.scores[c.name] - low) / (high - low)
                if high != low and not c.higher_is_better:
                    value = 1 - value
                result[a.name][c.name] = value * c.weight / self._weight_sum
        return result

    def design(self, alternatives):
        parts = self.contributions(alternatives)
        return sorted(((name, sum(values.values())) for name, values in parts.items()),
                      key=lambda pair: (-pair[1], pair[0]))

    def choice(self, ranking):
        if not ranking:
            raise ValueError('Cannot choose from an empty ranking.')
        best_name, best_score = ranking[0]
        tied = tuple(name for name, score in ranking if isclose(score, best_score, abs_tol=1e-12))
        if best_score < self.choice_threshold or best_score <= 1e-12:
            return Recommendation('CHUA_QUYET', ranking,
                'No recommendation: score is below threshold or the criteria do not distinguish alternatives.',
                tied=tied)
        return Recommendation(best_name, ranking,
            f'Highest relative priority score: {best_score:.4f}. '
            + (f'{len(tied)} authorities share first place.' if len(tied) > 1 else 'One authority ranks first.'),
            tied=tied)

    def recommend(self, alternatives):
        ready = self.intelligence(alternatives)
        result = self.choice(self.design(ready))
        parts = self.contributions(ready)
        return Recommendation(result.chosen, result.ranking, result.reason, parts, result.tied,
            tuple(a.name for a in alternatives if a not in ready))

if __name__ == '__main__':
    from run import main
    raise SystemExit(main())
