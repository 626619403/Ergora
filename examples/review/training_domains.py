"""Build two CPU arithmetic examples and exact packets; no model or training run.

Run with the installed Ergora interpreter from a checkout:
  python examples/review/training_domains.py --directory ./training-review-demo
"""

import argparse
from fractions import Fraction
import json
import math
import os
from pathlib import Path
import subprocess

from ergora import review_packets


def git(repository: Path, *arguments: str) -> str:
    environment = {key: value for key, value in os.environ.items() if not key.upper().startswith('GIT_')}
    environment.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT='0')
    result = subprocess.run(['git', '-c', 'core.hooksPath=' + os.devnull, '-c', 'core.autocrlf=false',
        '-c', 'commit.gpgsign=false', '-c', 'user.name=Ergora CPU Example',
        '-c', 'user.email=example@example.invalid', '-C', str(repository), *arguments],
        env=environment, check=True, capture_output=True, timeout=30)
    return result.stdout.decode('utf-8').strip()


def commit(repository: Path, message: str) -> str:
    git(repository, 'add', '.')
    git(repository, 'commit', '-qm', message)
    return git(repository, 'rev-parse', 'HEAD')


def evaluate(repository: Path, commit_id: str) -> dict:
    """Execute only these known example functions, not arbitrary project code."""
    import sys

    program = git(repository, 'show', commit_id + ':loss.py')
    configuration = json.loads(git(repository, 'show', commit_id + ':config.json'))
    # An isolated interpreter receives the authored example in stdin. The packet
    # collector itself never evaluates any code or runs a check.
    command = program + '\nimport json\nprint(json.dumps({"value": objective(' + repr(configuration) + ')}))\n'
    result = subprocess.run([sys.executable, '-I', '-'], input=command.encode('utf-8'),
                            check=True, capture_output=True, timeout=10)
    return json.loads(result.stdout)


def build(directory: Path, domain: str) -> dict:
    root = directory / domain
    repository = root / 'source'
    repository.mkdir(parents=True)
    git(repository, 'init', '-q', '--initial-branch=main')
    if domain == 'pretraining':
        correct = ('def objective(config):\n'
                   '    batches = config["batches"]\n'
                   '    return sum(sum(batch) for batch in batches) / sum(len(batch) for batch in batches)\n')
        regression = ('def objective(config):\n'
                      '    batches = config["batches"]\n'
                      '    return sum(sum(batch) / len(batch) for batch in batches) / len(batches)\n')
        baseline_config = {'batches': [[1], [4, 9, 16]]}
        valid_config = {'batches': [[1, 4, 9], [16]]}
        # Independent hand-derived oracle: the same four effective token terms
        # have numerator 30 and denominator 4, regardless of microbatch grouping.
        expected = Fraction(30, 4)
        requirement = ('The reported loss is the equally weighted mean of every effective token contribution. '
            'The four contributions are unchanged; microbatch grouping may vary. Review only this scalar reduction '
            'and its configuration/caller. No gradient, distributed, quality, convergence or performance claim is made.\n')
    else:
        correct = ('def objective(config):\n'
                   '    terms, mask = config["terms"], config["response_mask"]\n'
                   '    return sum(value * used for value, used in zip(terms, mask)) / sum(mask)\n')
        regression = ('def objective(config):\n'
                      '    terms = config["terms"]\n'
                      '    return sum(terms) / len(terms)\n')
        baseline_config = {'terms': [100, 100, 2, 4], 'response_mask': [0, 0, 1, 1]}
        valid_config = {'terms': [400, 2, 4, 300, 200], 'response_mask': [0, 1, 1, 0, 0]}
        # Independent hand-derived oracle: only response terms 2 and 4 contribute.
        expected = Fraction(6, 2)
        requirement = ('This example reports a mean of fixed supplied response-token surrogate contributions. '
            'Prompt/padding terms have zero response_mask and cannot affect the numerator or denominator. '
            'Only response terms 2 and 4 contribute; extra masked terms and their placement may vary. '
            'Review this scalar feedback/mask boundary; the estimator itself and rollout versions are outside '
            'this example. No PPO/GRPO, distributed, convergence, quality or performance validation is claimed.\n')
    (repository / 'AGENTS.md').write_text('Changes may affect loss.py or config.json. Preserve the stated objective; '
        'run.py is the small caller and uses only the declared configuration.\n', encoding='utf-8')
    (repository / 'loss.py').write_text(correct, encoding='utf-8')
    (repository / 'config.json').write_text(json.dumps(baseline_config, indent=2) + '\n', encoding='utf-8')
    (repository / 'run.py').write_text('import json\nfrom pathlib import Path\nfrom loss import objective\n'
        'print(objective(json.loads(Path(__file__).with_name("config.json").read_text())))\n', encoding='utf-8')
    base = commit(repository, 'fixed CPU contract')
    (repository / 'loss.py').write_text(regression, encoding='utf-8')
    bad = commit(repository, 'reduction change')
    git(repository, 'checkout', '-qb', 'configuration-variant', base)
    (repository / 'config.json').write_text(json.dumps(valid_config, indent=2) + '\n', encoding='utf-8')
    valid = commit(repository, 'configuration variant')
    values = {label: evaluate(repository, sha)['value'] for label, sha in [('base', base), ('regression', bad), ('valid', valid)]}
    expected_value = float(expected)
    if (not math.isclose(values['base'], expected_value, rel_tol=0, abs_tol=1e-12)
            or not math.isclose(values['valid'], expected_value, rel_tol=0, abs_tol=1e-12)
            or math.isclose(values['regression'], expected_value, rel_tol=0, abs_tol=1e-12)):
        raise ValueError('Example no longer demonstrates the independently specified CPU contract')
    request = root / 'request.md'
    request.write_text(requirement, encoding='utf-8')
    packets = {}
    for label, head in [('regression', bad), ('valid', valid)]:
        check = root / (label + '-check.json')
        check.write_text(json.dumps({'scope': 'authored CPU arithmetic example; not training',
            'base': base, 'head': head, 'expected_fraction': str(expected),
            'baseline_value': values['base'], 'candidate_value': values[label],
            'matches_scalar_contract': math.isclose(values[label], expected_value, rel_tol=0, abs_tol=1e-12)}, indent=2) + '\n')
        packets[label] = review_packets.prepare(repository, repository_id='example/' + domain,
            base=base, head=head, requirements=request, context_paths=['config.json', 'loss.py', 'run.py'],
            evidence=[check], destination=root / (label + '-packet'))
    return {'domain': domain, 'base': base, 'regression': bad, 'valid': valid,
            'expected_fraction': str(expected), 'values': values, 'packets': packets}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True, help='New persistent directory for the complete CPU examples')
    options = parser.parse_args()
    directory = options.directory.expanduser().absolute()
    directory.mkdir(parents=True, exist_ok=False)
    results = [build(directory, domain) for domain in ('pretraining', 'posttraining')]
    (directory / 'examples.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'directory': str(directory), 'examples': results}, indent=2))


if __name__ == '__main__':
    main()
