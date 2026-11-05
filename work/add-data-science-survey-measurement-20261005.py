"""Add an original survey-measurement sequence to Data Science."""
import datetime
import html
import json
import re
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
slugs = (
    'survey-construct-and-recall-window',
    'response-options-and-ordinal-coding',
    'cognitive-pilot-and-branch-logic-audit',
    'question-version-and-order-effect-checks',
    'support-handoff-survey-measurement-project',
)
new_paths = {'data-science/' + slug for slug in slugs}
rows = [row for row in rows if row['path'] not in new_paths]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
lessons = []

def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='data-science/' + slug, title=title, summary=summary,
                        sections=sections, code=code, cost=cost,
                        mistakes=mistakes, related=related))

add('survey-construct-and-recall-window',
    'Survey constructs, response units and recall windows',
    'A survey item is a measurement rule: define the construct, who can answer it and the period the answer covers.', [
    ('Define the construct before drafting', 'A support team wants to know whether a customer handoff was clear. “How happy were you with support?” measures a broader impression; it cannot isolate handoff clarity. A narrower item asks about the most recent handoff between support teams. Its target is the respondent’s reported understanding of the next step after that handoff. This remains self-report, not a direct measure of actual resolution quality. [[data-science/proxy-measurement-and-label-error|Proxy measurement]] explains why the distinction matters.'),
    ('Set a response unit', 'Choose one eligible support case and one customer contact as the response unit. If a customer has three cases, the invitation must name the selected case; otherwise different respondents may describe different experiences. The analysis table needs a case key, invitation key, survey version and answer timestamp. Do not let repeated clicks create duplicate respondents. [[data-science/dataset-grain-and-join-cardinality|Dataset grain]] keeps invitation and response counts separate.'),
    ('Make the recall period answerable', 'Ask about a handoff in the last 14 days and show the case date. A respondent who cannot recall the event needs an explicit option, not a forced guess. Short recall windows can improve specificity but may reduce eligible sample size; long windows increase coverage while making memory errors more likely. Document the tradeoff and keep the same window when comparing periods. An answer collected after a policy change may describe an older experience.'),
    ('Remove implied judgment', 'A question such as “Why did our helpful agent make the handoff easy?” presumes both helpfulness and ease. Ask one idea at a time: “After the handoff, how clear was the next step?” Then separately ask whether the next step actually occurred. Avoid naming a desired answer in the invitation. Test the item with people who experienced a handoff, including those whose case was unresolved.'),
    ('Write a measurement contract', 'Store item text, displayed context, eligibility, language, recall window, permitted answers and analysis interpretation under a version ID. If the item changes, retain both versions in raw data. [[data-science/response-options-and-ordinal-coding|Response options]] may change the meaning as much as the question wording. A report should say “reported handoff clarity among respondents,” not “handoff quality among all customers,” unless coverage and response assumptions support that stronger claim.')],
    'from datetime import date\n\ndef eligible_handoff_case(handoff_date, invitation_date, days=14):\n    if days <= 0:\n        raise ValueError("recall window must be positive")\n    elapsed = (invitation_date - handoff_date).days\n    return 0 <= elapsed <= days\n\ninvitation = date(2026, 9, 27)\nassert eligible_handoff_case(date(2026, 9, 18), invitation)\nassert not eligible_handoff_case(date(2026, 9, 2), invitation)\nassert not eligible_handoff_case(date(2026, 9, 28), invitation)',
    'Eligibility checking is O(1) per case and O(N) for N invitations. Joining responses to cases may dominate runtime and must preserve the one-case response unit. The main cost is question testing and maintaining versioned measurement definitions.',
    ['Do not report self-reported clarity as verified resolution quality.', 'Do not let each respondent choose an unspecified handoff event.', 'Do not change recall windows between reporting periods without flagging the break.'],
    ['data-science/response-options-and-ordinal-coding','data-science/cognitive-pilot-and-branch-logic-audit','data-science/question-version-and-order-effect-checks','data-science/support-handoff-survey-measurement-project'])

add('response-options-and-ordinal-coding',
    'Response options and ordinal coding without false precision',
    'Response categories define what a survey result can mean; preserve their order, labels and special states before analysis.', [
    ('Match categories to the question', 'For handoff clarity, a five-category scale can run from “not at all clear” through “completely clear.” Each label should refer to clarity, not switch midway to satisfaction or trust. Offer “I do not remember” and “no handoff occurred” only when those states are possible and meaningful. They are not the midpoint. A respondent who never experienced a handoff may be ineligible for the item rather than a low-clarity answer.'),
    ('Keep non-substantive states distinct', 'A blank response, a deliberate skip, a displayed “do not remember” choice and a branch that never displayed the item are four separate data states. Encoding all as zero creates a fake low category. Build a codebook with stable string IDs and display labels. If labels are translated, retain the source version and language so category mapping can be audited. [[data-science/missingness-mechanisms-and-observation-process|Missingness mechanisms]] still apply to survey items.'),
    ('Respect ordinal data', 'The order from unclear to clear is meaningful, but the distance between adjacent labels is not guaranteed equal. Report category shares and a predeclared top-two share before treating numeric scores as interval measurements. If a mean is used for operational convenience, say that equal spacing is an assumption and show whether the decision changes under category shares. A shift from mostly clear to completely clear need not have the same magnitude as a shift from unclear to somewhat clear.'),
    ('Preserve the denominator', 'Suppose 31 respondents completed the survey, but only 27 saw the handoff item and 23 gave a substantive clarity answer. A top-two count of 17 is 17/23 among substantive answers, not 17/31 among all respondents or 17/53 among invitees. Show each denominator and why four item displays lack a substantive answer. [[data-science/metric-denominator-and-cohort|Denominator contracts]] keep the comparison reviewable.'),
    ('Version category changes', 'Adding a neutral midpoint, changing its label or moving a “do not know” option can alter the response distribution. Do not silently merge old and new data. Retain raw category IDs, make a documented crosswalk if defensible, and display distributions by form version. [[data-science/question-version-and-order-effect-checks|Version checks]] separate a measurement change from a service change.')],
    'from collections import Counter\n\ndef clarity_distribution(answer_ids):\n    substantive = {"not_clear", "slightly_clear", "moderately_clear",\n                   "mostly_clear", "completely_clear"}\n    special = {"do_not_remember", "not_applicable", "skipped", "not_displayed"}\n    counts = Counter(answer_ids)\n    unknown = set(counts) - substantive - special\n    if unknown:\n        raise ValueError(f"unrecognized answers: {sorted(unknown)}")\n    answered = sum(counts[answer] for answer in substantive)\n    top_two = counts["mostly_clear"] + counts["completely_clear"]\n    return {"answered": answered, "top_two": top_two,\n            "top_two_share": top_two / answered if answered else None,\n            "special_counts": {answer: counts[answer] for answer in special}}\n\nresult = clarity_distribution(["mostly_clear", "completely_clear",\n                               "do_not_remember", "not_displayed"])\nassert result["answered"] == 2 and result["top_two_share"] == 1.0',
    'Counting N answers uses O(N) time and O(K) space for K categories. The fixed category set makes K bounded. Keep raw records and version metadata; an aggregate alone cannot reveal whether a branch or label changed.',
    ['Do not code “do not remember” as a neutral clarity score.', 'Do not divide a substantive-answer count by all invitations without labeling the result.', 'Do not assume equal distances between ordinal response categories.'],
    ['data-science/survey-construct-and-recall-window','data-science/cognitive-pilot-and-branch-logic-audit','data-science/question-version-and-order-effect-checks','data-science/support-handoff-survey-measurement-project'])

add('cognitive-pilot-and-branch-logic-audit',
    'Cognitive pilots and survey branch-logic audits',
    'A pilot should reveal how people interpret an item and whether the form displays it to the right respondents.', [
    ('Test interpretation before rates', 'Recruit a small set of people resembling the intended respondents, including recent handoff cases and people without a handoff. Ask them to complete the form and explain what “next step” meant in their own case. If one respondent thinks it refers to the agent’s next step and another to the customer’s, the item is not yet stable. A pilot of nine people can reveal such problems, but it is not a precision estimate for the full population.'),
    ('Log the question path', 'The item “How clear was the next step after the handoff?” should display only when the respondent confirms that a handoff occurred. The form must preserve the branch variable and a not-displayed state. An API payload with handoff=false and a substantive clarity answer is internally inconsistent; reject or quarantine it rather than quietly including it. [[data-science/response-options-and-ordinal-coding|Response states]] make this validation explicit.'),
    ('Record observed problems', 'Capture issue codes such as ambiguous reference, missing response option, faulty branch, excessive recall demand and inaccessible wording. Keep the respondent’s explanation separately from the researcher’s interpretation. If five of nine pilot respondents misread one item, that is a signal to revise it; it is not an estimate that 55.6% of future respondents will misread it. Qualitative pilots find mechanisms, not population rates.'),
    ('Retest after revision', 'Changing the wording can repair one ambiguity and introduce another. Re-run the affected branch and translation with new participants or a second pilot wave. Test a keyboard-only path, mobile layout, the “no handoff” branch and incomplete submissions. Save the old and new item versions. [[data-science/survey-construct-and-recall-window|The measurement contract]] should document why a change was made.'),
    ('Set a release gate', 'Before fielding, require no unresolved critical branch defect, a readable codebook, a declared eligible population and a planned response-rate report. Check that the survey platform records form version and assignment. This gate does not certify absence of response bias; [[data-science/nonresponse-bias-and-follow-up|nonresponse analysis]] starts once invitations are sent.')],
    'def validate_handoff_response(response):\n    handoff = response["handoff_occurred"]\n    clarity = response["clarity_answer"]\n    if handoff is False and clarity != "not_displayed":\n        return "invalid_branch"\n    if handoff is True and clarity == "not_displayed":\n        return "missing_display"\n    if handoff not in (True, False):\n        return "unknown_handoff_status"\n    return "valid"\n\nassert validate_handoff_response({"handoff_occurred": False,\n                                  "clarity_answer": "not_displayed"}) == "valid"\nassert validate_handoff_response({"handoff_occurred": False,\n                                  "clarity_answer": "mostly_clear"}) == "invalid_branch"',
    'Validating N responses costs O(N) time and O(1) working space for a streaming checker. Qualitative interview review is a separate human task whose cost depends on participant diversity, form branches and the number of revisions.',
    ['Do not use a tiny cognitive pilot as a population prevalence estimate.', 'Do not repair an invalid branch by silently recoding the substantive answer.', 'Do not skip retesting after a wording or logic change.'],
    ['data-science/survey-construct-and-recall-window','data-science/response-options-and-ordinal-coding','data-science/question-version-and-order-effect-checks','data-science/support-handoff-survey-measurement-project'])

add('question-version-and-order-effect-checks',
    'Question versions, order effects and comparable trends',
    'Changing an item, its position or the survey mode can change answers without changing the underlying experience.', [
    ('Treat the form as an instrument', 'A handoff-clarity item may follow a complaint question in one version and a factual case-date question in another. Earlier questions can frame what respondents consider when answering. A mobile form may also show response options differently from a phone script. Store item text, option labels, order, device or mode, and release version for each response. [[data-science/instrumentation-change-and-metric-guardrails|Instrumentation changes]] can break a trend just as event-schema changes can.'),
    ('Design a split before release', 'When a revision is needed, randomly assign eligible invitations within the same field period to form A or B. Keep the case-selection process, reminder policy and outcome window aligned. For an example pilot, 16 responses to A include six top-two answers and 15 responses to B include three. These are observed shares of 6/16 and 3/15 among respondents, not proof of a wording effect or a population trend. Assignment integrity and response patterns must be checked first.'),
    ('Check exposure and response', 'Report invitations by assigned form, delivered invitations, starts, completed responses and substantive item answers. Random assignment at invitation does not guarantee that respondent subsets remain comparable if one version discourages completion. Compare response rates and known pre-invitation case attributes by form. [[data-science/nonresponse-bias-and-follow-up|Follow-up analysis]] addresses who did not answer; the split alone does not remove response selection.'),
    ('Avoid a naive splice', 'Do not join old-form and new-form percentages into one time series and call the difference a service change. If a randomized overlap period supports a defensible bridge, show both raw series and the adjustment with uncertainty. If no overlap exists, mark a measurement break. A correlation between forms does not show that individual answers are interchangeable, especially when response categories changed.'),
    ('Preserve the comparison packet', 'Save randomization unit, assignment seed or system log, field dates, question versions, codebooks, denominator counts and analysis code. Predeclare the primary outcome and what difference would trigger keeping the old item, revising the new one or treating the series as broken. [[data-science/reproducible-analysis-snapshot|A reproducible snapshot]] lets an analyst inspect the exact version each respondent saw.')],
    'def form_response_funnel(invited_by_form, completed_by_form):\n    report = {}\n    for form_version, invited in invited_by_form.items():\n        completed = completed_by_form.get(form_version, 0)\n        if invited <= 0 or not 0 <= completed <= invited:\n            raise ValueError("invalid invitation or completion count")\n        report[form_version] = {"invited": invited, "completed": completed,\n                                "response_share": completed / invited}\n    if set(completed_by_form) - set(invited_by_form):\n        raise ValueError("completion without a known form assignment")\n    return report\n\nfunnel = form_response_funnel({"A": 27, "B": 26}, {"A": 16, "B": 15})\nassert funnel["A"]["completed"] + funnel["B"]["completed"] == 31',
    'For F form versions, count reconciliation is O(F) time and output space. Assignment and outcome analysis over N invitees is O(N). A credible comparison depends more on exposure and response logs than on computing two percentages.',
    ['Do not infer a wording effect from respondent-only percentages after unequal nonresponse.', 'Do not splice item versions into one trend without an overlap study or a marked break.', 'Do not randomize form versions after seeing a respondent’s answers.'],
    ['data-science/survey-construct-and-recall-window','data-science/response-options-and-ordinal-coding','data-science/cognitive-pilot-and-branch-logic-audit','data-science/support-handoff-survey-measurement-project'])

add('support-handoff-survey-measurement-project',
    'Project: measure support-handoff clarity with a versioned survey',
    'Create a survey audit that preserves the case frame, item meaning, branch states and form-version comparability.', [
    ('Build the invitation frame', 'Select 53 eligible support cases with a handoff in the previous 14 days, one contact per case. Preserve invitation ID, case ID, handoff date, queue, form assignment and delivery status. Record exclusions before invitation. The response file contains 31 completed surveys and 22 nonresponses; those counts must reconcile to the eligible frame. [[data-science/sampling-frame-and-coverage-error|Frame checks]] determine who could be represented.'),
    ('Specify and pilot the measure', 'Ask one neutral question about how clear the next step was after the named handoff. Use ordered clarity labels, plus explicit “do not remember” and a not-displayed state for the no-handoff branch. Run a nine-person cognitive pilot that includes both handoff and no-handoff experiences. Log ambiguous interpretations and branch defects, revise, and retest. [[data-science/cognitive-pilot-and-branch-logic-audit|Pilot checks]] produce a release decision, not a population estimate.'),
    ('Reconcile response states', 'Suppose 27 respondents saw the item and 23 gave a substantive clarity answer; 17 of those chose the top two categories. Report 17/23 as the top-two share among substantive item answers, alongside 23/27 substantive completion and 31/53 survey completion. Do not bury four non-substantive item responses in the top-two denominator. [[data-science/response-options-and-ordinal-coding|The codebook]] keeps skip, non-display and recall failure distinct.'),
    ('Run a version overlap', 'Assign 27 invitations to form A and 26 to form B before fielding. In the fixture, A yields 16 completed responses and B yields 15. Keep exact wording, order and option IDs for both forms. Compare invitation, response and item-answer counts before comparing their clarity distributions. [[data-science/question-version-and-order-effect-checks|The version lesson]] explains why respondent-only differences are not automatically wording effects.'),
    ('Deliver an honest report', 'Publish the survey contract, frame counts, pilot issue log, form version map, branch-validity results, category distribution, respondent-only estimate and nonresponse caveat. Investigate whether nonrespondents differ on known case attributes. If a form revision is not comparable, mark the trend break and keep both versions in the export. [[data-science/nonresponse-bias-and-follow-up|Nonresponse follow-up]] is a separate analysis task.')],
    'def reconcile_survey(invitation_ids, completed_ids, substantive_answers):\n    invitations = set(invitation_ids)\n    completions = set(completed_ids)\n    if len(invitations) != len(invitation_ids):\n        raise ValueError("duplicate invitation IDs")\n    if len(completions) != len(completed_ids) or not completions <= invitations:\n        raise ValueError("invalid completed response IDs")\n    if not 0 <= substantive_answers <= len(completions):\n        raise ValueError("invalid substantive answer count")\n    return {"invited": len(invitations), "completed": len(completions),\n            "nonresponse": len(invitations - completions),\n            "substantive_answers": substantive_answers}\n\npacket = reconcile_survey(range(53), range(31), 23)\nassert packet == {"invited": 53, "completed": 31,\n                  "nonresponse": 22, "substantive_answers": 23}',
    'Set reconciliation costs O(I + R) time and space for I invitations and R response IDs. Category summaries are O(R). The costly step is establishing what the question measures and whether the respondent frame supports the intended claim.',
    ['Do not label respondent-only clarity as the opinion of all 53 invitees.', 'Do not merge form versions without a comparability check.', 'Do not delete invalid branch records before recording the defect rate.'],
    ['data-science/survey-construct-and-recall-window','data-science/response-options-and-ordinal-coding','data-science/cognitive-pilot-and-branch-logic-audit','data-science/question-version-and-order-effect-checks'])

assert len(lessons) == len(new_paths) == 5
assert {item['path'] for item in lessons} == new_paths
titles = {path: row['title'] for path, row in by_path.items()}
titles.update({item['path']: item['title'] for item in lessons})

def prose(value):
    return re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
                  lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                  html.escape(value))

def links(paths):
    return '<ul>' + ''.join('<li><a href="/' + path + '">' + html.escape(titles[path]) + '</a></li>'
                            for path in paths) + '</ul>'

def article_body(item):
    parts = ['<p>' + html.escape(item['summary']) + '</p>']
    for heading, paragraph in item['sections']:
        parts.extend(('<h2>' + html.escape(heading) + '</h2>', '<p>' + prose(paragraph) + '</p>'))
    parts.extend(('<h2>Implementation</h2>',
                  '<pre><code class="language-python">' + html.escape(item['code']) + '</code></pre>',
                  '<h2>Performance and operating cost</h2>', '<p>' + html.escape(item['cost']) + '</p>',
                  '<h3>Common Mistakes</h3>',
                  '<ul>' + ''.join('<li>' + html.escape(mistake) + '</li>' for mistake in item['mistakes']) + '</ul>',
                  '<h2>Read next</h2>', links(item['related'])))
    return ''.join(parts)

root_path = 'data-science/data-science-for-beginners'
project_hub_path = root_path + '/project'
for index, item in enumerate(lessons):
    is_project = item['path'].endswith('-project')
    body = article_body(item)
    path = item['path']
    row = dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)),
               type='article', path=path, title=item['title'], summary=item['summary'], body=body,
               category='AI & Data', subject='data-science-project' if is_project else 'data-science',
               difficulty='Intermediate', tags=['ai-data', 'data-science'], potd_date=None,
               featured=False, sort_order=12500 + index, status='published', published_at=stamp,
               created_at=stamp, updated_at=stamp,
               data={'subject_root':root_path,
                     'section_path':project_hub_path if is_project else root_path,
                     'content_format':'html', 'seo_ready':True,
                     'kind':'project' if is_project else 'tutorial',
                     'reading_minutes':max(5, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                     'author_path':'authors/aitrove-editorial',
                     'verification_suite':'Editorial and syntax review; project inputs needed for runtime checks',
                     'related':[{'path':target, 'title':titles[target]} for target in item['related']]})
    rows.append(row)
    by_path[path] = row

tutorial_paths = ['data-science/' + slug for slug in slugs[:4]]
project_path = 'data-science/' + slugs[-1]
hub = by_path[root_path]
module_paths = {path for module in hub['data']['modules'] for path in module['lessons']}
if not set(tutorial_paths).issubset(module_paths):
    hub['data']['modules'].insert(-1, {'title':'Survey measurement and form quality',
                                      'summary':'Define the survey construct, code response states, test the form and preserve comparable versions.',
                                      'lessons':tutorial_paths})
apply_module = next(module for module in hub['data']['modules'] if module['title'] == 'Apply your knowledge')
if project_path not in apply_module['lessons']:
    apply_module['lessons'].append(project_path)
if '<h2>Survey measurement and form quality</h2>' not in hub['body']:
    hub['body'] += ('<h2>Survey measurement and form quality</h2>' + links(tutorial_paths)
                    + '<h2>Support handoff survey project</h2>' + links([project_path]))
hub['updated_at'] = stamp

project_hub = by_path[project_hub_path]
if project_path not in project_hub['data']['modules'][0]['lessons']:
    project_hub['data']['modules'][0]['lessons'].append(project_path)
if '<h2>Support handoff survey project</h2>' not in project_hub['body']:
    project_hub['body'] += '<h2>Support handoff survey project</h2>' + links([project_path])
project_hub['updated_at'] = stamp

for source, target in [
    ('data-science/proxy-measurement-and-label-error', tutorial_paths[0]),
    ('data-science/missing-data-policy', tutorial_paths[1]),
    ('data-science/nonresponse-bias-and-follow-up', tutorial_paths[2]),
    ('data-science/instrumentation-change-and-metric-guardrails', tutorial_paths[3]),
    ('data-science/support-resolution-cohort-project', project_path),
]:
    source_row = by_path[source]
    anchor = '<p><strong>Continue the workflow:</strong> <a href="/' + target + '">' + html.escape(titles[target]) + '</a>.</p>'
    if anchor not in source_row['body']:
        source_row['body'] += anchor
        if source_row['type'] == 'article':
            source_row['data'].setdefault('related', []).append({'path':target, 'title':titles[target]})
        source_row['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_articles':len(lessons), 'new_projects':1, 'crosslinks_from_existing':5}))
