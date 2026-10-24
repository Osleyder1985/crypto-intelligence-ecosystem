"""Evidence-gated weighted scoring and one-at-a-time sensitivity analysis."""
import argparse
import json
from pathlib import Path


def analyze(payload):
    weights = payload.get('weights', {})
    candidates = payload.get('candidates', [])
    if not weights or not candidates:
        raise ValueError('weights and candidates are required')
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0 for v in weights.values()):
        raise ValueError('weights must be positive numbers')
    if abs(sum(weights.values()) - 100.0) > 1e-6:
        raise ValueError('weights must sum to 100')

    missing = []
    normalized = {}
    candidate_names = [candidate.get('name') for candidate in candidates]
    if any(not isinstance(name, str) or not name.strip() for name in candidate_names):
        raise ValueError('each candidate needs a non-empty name')
    if len(candidate_names) != len(set(candidate_names)):
        raise ValueError('candidate names must be unique')
    for candidate in candidates:
        name = candidate.get('name')
        scores = candidate.get('scores', {})
        evidence = candidate.get('evidence', {})
        if not name:
            raise ValueError('each candidate needs a name')
        for criterion in weights:
            score = scores.get(criterion)
            ref = evidence.get(criterion)
            if isinstance(score, bool) or not isinstance(score, int) or score < 1 or score > 5 or not isinstance(ref, str) or not ref.strip():
                missing.append({'candidate': name, 'criterion': criterion, 'score': score, 'evidence': ref})
        normalized[name] = {'scores': scores, 'evidence': evidence}

    if missing:
        return {'status': 'incomplete', 'reason': 'Scores require a 1–5 value and a non-empty evidence reference for every criterion.', 'missing': missing, 'ranking': [], 'sensitivity': []}

    def totals(active_weights):
        denom = sum(active_weights.values())
        return {name: sum(active_weights[k] * item['scores'][k] / 5 for k in active_weights) / denom for name, item in normalized.items()}

    baseline = totals(weights)
    baseline_order = [name for name, _ in sorted(baseline.items(), key=lambda item: (-item[1], item[0]))]
    sensitivity = []
    for criterion, original in weights.items():
        for factor in (0.8, 1.2):
            changed = dict(weights)
            changed[criterion] = original * factor
            scores = totals(changed)
            order = [name for name, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))]
            sensitivity.append({'criterion': criterion, 'factor': factor, 'ranking': order, 'ranking_changed': order != baseline_order, 'scores': scores})
    return {'status': 'complete', 'ranking': [{'candidate': name, 'score_out_of_100': round(baseline[name], 4)} for name in baseline_order], 'sensitivity': sensitivity, 'ranking_stable': all(not row['ranking_changed'] for row in sensitivity)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = analyze(json.loads(args.input.read_text(encoding='utf-8')))
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
    if args.output:
        args.output.write_text(rendered, encoding='utf-8')
    print(rendered, end='')
    return 0 if result['status'] == 'complete' else 2


if __name__ == '__main__':
    raise SystemExit(main())
