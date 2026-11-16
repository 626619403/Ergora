"""Pure inspection of declared design content, without approval or file authority.

Callers validate JSON structure and safely read bytes before entering this module.
No packet field authenticates a policy, owner, response or resolution.
"""

from datetime import datetime


def inspect_packet(packet: dict, profile: dict, expected: dict, sources: dict,
                   work_unit_ids: list | None = None) -> dict:
    """Check references and report exact Q/K gaps under an inspection profile.

    The current caller has no trusted response chain or frozen design policy.
    Consequently even intact, complete content cannot be ready for approval.
    """
    blockers, integrity = [], []

    def issue(target: list, kind: str, item_id: str, path: str, code: str, **details) -> None:
        target.append({'kind': kind, 'id': item_id, 'path': path, 'code': code, **details})

    groups = {name: {} for name in ('requirements', 'sections', 'source_records', 'questions',
                                    'knowledge_requirements', 'acceptance_criteria', 'implementation_steps',
                                    'research_adoption', 'existing_structure', 'changes', 'alternatives', 'standards')}
    seen = set()
    for name, items in groups.items():
        for index, item in enumerate(packet[name]):
            if item['id'] in seen:
                issue(integrity, 'reference', item['id'], f'/{name}/{index}/id', 'duplicate_id')
            seen.add(item['id'])
            items[item['id']] = item

    def references(names: list, group: str, path: str, item_id: str) -> None:
        for name in names:
            if name not in groups[group]:
                issue(integrity, 'reference', item_id, path, 'unknown_reference', reference=name, group=group)

    for field, value in expected.items():
        if packet[field] != value:
            issue(integrity, 'binding', field, '/' + field, 'original_binding_mismatch')
    if (packet['revision'] == 1) != (packet['previous_packet_sha256'] is None):
        issue(integrity, 'binding', 'revision', '/previous_packet_sha256', 'invalid_previous_revision')

    for section_id in profile['required_sections']:
        if section_id not in groups['sections']:
            issue(blockers, 'section', section_id, '/sections', 'missing_section')

    for index, section in enumerate(packet['sections']):
        references(section['basis_refs'], 'source_records', f'/sections/{index}/basis_refs', section['id'])
    for index, entry in enumerate(packet['research_adoption']):
        references(entry['source_refs'], 'source_records', f'/research_adoption/{index}/source_refs', entry['id'])
    for index, entry in enumerate(packet['existing_structure']):
        references(entry['basis_refs'], 'source_records', f'/existing_structure/{index}/basis_refs', entry['id'])
    for index, entry in enumerate(packet['standards']):
        references(entry['basis_refs'], 'source_records', f'/standards/{index}/basis_refs', entry['id'])
    references(packet['direction_refs'], 'source_records', '/direction_refs', 'direction')
    references([packet['report_ref']], 'source_records', '/report_ref', 'report')
    if packet['html_ref'] is not None:
        references([packet['html_ref']], 'source_records', '/html_ref', 'html')
    for name, media_type in (('report_ref', 'text/markdown'), ('html_ref', 'text/html')):
        source = groups['source_records'].get(packet[name])
        if source is not None and (source['access'] != 'full' or source['source_type'] != 'report'):
            issue(integrity, 'source', source['id'], '/' + name, 'report_requires_full_text')
        elif source is not None and source['body']['media_type'] != media_type:
            issue(integrity, 'source', source['id'], '/' + name, 'report_media_type_mismatch',
                  expected_media_type=media_type, actual_media_type=source['body']['media_type'])

    minimum = {item['id']: item for item in profile['minimum_questions']}
    for question_id in minimum:
        if question_id not in groups['questions']:
            issue(blockers, 'question', question_id, '/questions', 'missing_question',
                  required_by=[profile['id']], next_action='provide_question')
    for index, question in enumerate(packet['questions']):
        path, question_id = f'/questions/{index}', question['id']
        references(question['requirement_ids'], 'requirements', path + '/requirement_ids', question_id)
        references(question['basis_refs'], 'source_records', path + '/basis_refs', question_id)
        references(question['affected_sections'], 'sections', path + '/affected_sections', question_id)
        if question['introduced_revision'] > packet['revision']:
            issue(integrity, 'question', question_id, path + '/introduced_revision', 'future_revision')
        if question['owner_id'] != packet['owner_id']:
            issue(integrity, 'question', question_id, path + '/owner_id', 'inconsistent_declared_owner')
        if question_id in minimum:
            if any(question[key] != minimum[question_id][key] for key in ('body', 'why_required')):
                issue(integrity, 'question', question_id, path, 'minimum_question_changed')
            if profile['id'] not in question['required_by']:
                issue(integrity, 'question', question_id, path + '/required_by', 'minimum_requirement_omitted')
        option_ids = [option['id'] for option in question['options']]
        if len(set(option_ids)) != len(option_ids):
            issue(integrity, 'question', question_id, path + '/options', 'duplicate_option_id')
        issue(blockers, 'question', question_id, path, 'unresolved', owner_id=question['owner_id'],
              affected_acceptance_ids=[item['id'] for item in packet['acceptance_criteria']
                                       if set(item['requirement_ids']) & set(question['requirement_ids'])],
              next_action='obtain_owner_response_and_trusted_resolution')

    for index, criterion in enumerate(packet['acceptance_criteria']):
        references(criterion['requirement_ids'], 'requirements',
                   f'/acceptance_criteria/{index}/requirement_ids', criterion['id'])
    for index, step in enumerate(packet['implementation_steps']):
        references(step['depends_on'], 'implementation_steps', f'/implementation_steps/{index}/depends_on', step['id'])
        references(step['acceptance_ids'], 'acceptance_criteria',
                   f'/implementation_steps/{index}/acceptance_ids', step['id'])
        if work_unit_ids is not None:
            for unit_id in step['work_unit_ids']:
                if unit_id not in work_unit_ids:
                    issue(integrity, 'work-unit', unit_id, f'/implementation_steps/{index}/work_unit_ids',
                          'unknown_original_work_unit')
    if work_unit_ids is not None:
        mapped = {unit for step in packet['implementation_steps'] for unit in step['work_unit_ids']}
        for unit_id in work_unit_ids:
            if unit_id not in mapped:
                issue(integrity, 'work-unit', unit_id, '/implementation_steps', 'unmapped_original_work_unit')

    observed_at, observations = {}, {name: dict(value) for name, value in sources.items()}
    for index, source in enumerate(packet['source_records']):
        observed_at[source['id']] = datetime.fromisoformat(source['observed_at'])
        if observed_at[source['id']].utcoffset() is None:
            raise ValueError('Design source observations require a timezone: ' + source['id'])
        observation = observations[source['id']]
        if observation['status'] == 'read':
            if observation['sha256'] != source['body']['sha256']:
                observation['status'] = 'digest_mismatch'
            elif observation['bytes'] != source['body']['bytes']:
                observation['status'] = 'byte_count_mismatch'
        if observation['status'] not in ('read', 'reference_only'):
            issue(integrity, 'source', source['id'], f'/source_records/{index}', observation['status'])
    supplied = []
    for index, knowledge in enumerate(packet['knowledge_requirements']):
        path, knowledge_id = f'/knowledge_requirements/{index}', knowledge['id']
        references(knowledge['affected_question_ids'], 'questions', path + '/affected_question_ids', knowledge_id)
        references(knowledge['affected_acceptance_ids'], 'acceptance_criteria', path + '/affected_acceptance_ids', knowledge_id)
        references(knowledge['supplied_refs'], 'source_records', path + '/supplied_refs', knowledge_id)
        references(knowledge['conflict_refs'], 'source_records', path + '/conflict_refs', knowledge_id)
        reasons = []
        if knowledge['status'] != 'supplied':
            reasons.append(knowledge['status'])
        if knowledge['conflict_refs']:
            reasons.append('conflicting')
        if not knowledge['supplied_refs']:
            reasons.append('missing_source')
        rule = knowledge['freshness_rule']
        if rule is not None:
            checked = datetime.fromisoformat(rule['observed_at'])
            if checked.utcoffset() is None:
                raise ValueError('Design freshness observations require a timezone: ' + knowledge_id)
        for ref in knowledge['supplied_refs']:
            source = groups['source_records'].get(ref)
            if source is None:
                reasons.append('unknown_source')
                continue
            if observations[ref]['status'] != 'read':
                reasons.append(observations[ref]['status'])
            if source['source_type'] not in knowledge['allowed_source_types']:
                reasons.append('disallowed_source_type')
            if source['access_scope_ref'] != knowledge['access_scope_ref']:
                reasons.append('access_scope_mismatch')
            if rule is not None:
                if rule['required_version'] is not None and source['version'] != rule['required_version']:
                    reasons.append('stale_version')
                if rule['max_age_seconds'] is not None:
                    age = (checked - observed_at[ref]).total_seconds()
                    if age < 0 or age > rule['max_age_seconds']:
                        reasons.append('stale')
        if reasons:
            issue(blockers, 'knowledge', knowledge_id, path, 'knowledge_unresolved', reasons=sorted(set(reasons)),
                  affected_question_ids=knowledge['affected_question_ids'],
                  affected_acceptance_ids=knowledge['affected_acceptance_ids'], next_action='provide_authorized_source_or_owner_decision')
        else:
            supplied.append(knowledge_id)

    return {'sources': observations, 'content_integrity': {'valid': not integrity, 'blockers': integrity},
            'declared_requirements': {'blockers': blockers, 'knowledge_supplied_ids': supplied,
                                      'knowledge_supplied_is_owner_decision': False},
            'readiness': {'ready': False, 'blockers': [*integrity, *blockers,
                {'kind': 'authority', 'id': 'design-policy', 'path': '/', 'code': 'frozen_design_policy_unavailable'},
                {'kind': 'authority', 'id': 'owner', 'path': '/owner_id', 'code': 'owner_channel_unavailable'}]}}
