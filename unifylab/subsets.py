"""Exhaustive indexed equation subsets, conservative under solver limits.

No monotonicity-based status inference. Only checked immediate neighbors can
establish an inclusion-minimal conflict or an inclusion-minimal deletion repair.
"""
from .core import validate, solve


def analyze(data):
    canonical, _, _ = validate(data)
    equations = canonical['equations']; n = len(equations); full = (1 << n) - 1
    indices = lambda mask: [i for i in range(n) if mask & (1 << i)]
    records = []
    for mask in range(full + 1):
        selected = indices(mask)
        report = solve({'equations': [equations[i] for i in selected]})
        records.append({'mask': mask, 'indices': selected, 'status': report['status'],
                        'failure': report['failure'], 'limit': report['limit'],
                        'rewrites': len(report['steps'])})
    cores = []; repairs = []
    for row in records:
        mask = row['mask']
        if row['status'] == 'not_unifiable':
            checks = [{'equation': i, 'neighbor_mask': mask ^ (1 << i),
                       'status': records[mask ^ (1 << i)]['status']} for i in row['indices']]
            if all(c['status'] == 'unified' for c in checks):
                cores.append({'mask': mask, 'indices': row['indices'], 'checks': checks})
        if row['status'] == 'unified':
            removed = full ^ mask
            checks = [{'equation': i, 'neighbor_mask': mask | (1 << i),
                       'status': records[mask | (1 << i)]['status']} for i in indices(removed)]
            if all(c['status'] == 'not_unifiable' for c in checks):
                repairs.append({'removed_mask': removed, 'removed_indices': indices(removed),
                                'kept_mask': mask, 'checks': checks})
    repairs.sort(key=lambda r: r['removed_mask'])
    unresolved = [r['mask'] for r in records if r['status'] == 'limit']
    complete = not unresolved
    return {'schema': 'unifylab-subsets-v1', 'input': canonical, 'records': records,
            'complete': complete, 'unresolved_masks': unresolved,
            'minimal_cores': cores, 'minimal_repairs': repairs,
            'minimum_core_size': min((len(c['indices']) for c in cores), default=None) if complete else None,
            'minimum_repair_size': min((len(r['removed_indices']) for r in repairs), default=None) if complete else None}
