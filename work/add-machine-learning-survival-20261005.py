"""Add original operational time-to-event machine learning lessons."""
from ml_fixture_writer_20261005 import publish_batch

lessons = []


def add(slug, title, summary, sections, code, cost, mistakes, related):
    lessons.append(dict(path='machine-learning/' + slug, title=title,
                        summary=summary, sections=sections, code=code,
                        cost=cost, mistakes=mistakes, related=related))


add('time-to-event-target-and-censor-contract',
    'Time-to-event targets and censoring contracts',
    'A survival target pairs elapsed time with event status; an unfinished observation contributes follow-up rather than an invented event or a negative outcome.', [
    ('Choose one time origin', 'A fleet operator wants to predict days from a vehicle’s scheduled inspection to a battery replacement. The origin is the inspection timestamp, not vehicle purchase or the day a data export was run. Define the event as a confirmed replacement work order, including how canceled orders and repeat replacements are treated. An inspection after replacement begins a new episode only if the business question permits it.'),
    ('Record what is known', 'For each eligible episode, store elapsed follow-up and whether replacement occurred by the last reliable observation. A vehicle still operating on day 71 is right-censored at day 71; its replacement time is unknown. Coding it as a day-71 failure biases early risk upward. Coding it as “never fails” removes the information that it survived 71 days. [[data-science/right-censoring-and-time-to-event|Right-censoring]] gives the statistical contract.'),
    ('Distinguish observation loss', 'Administrative cutoff at a common export date differs from losing access when a truck changes contractor. The latter may correlate with condition or mileage, violating simple independent-censoring assumptions. Track censor reason and compare its frequency by depot, vehicle age and maintenance status before model training.'),
    ('Freeze prediction-time inputs', 'A repair note created after battery replacement cannot predict replacement from inspection day. Snapshot odometer, voltage, route and service history as known at the inspection. Data pipelines must join by both entity and availability time. [[machine-learning/prediction-time-feature-availability|Feature availability]] prevents a clean-looking but unusable model.'),
    ('Declare supported horizons', 'If very few vehicles remain observed at 180 days, a 180-day risk claim is weak even when a model returns a number. Record at-risk counts and censoring by horizon. [[machine-learning/survival-risk-set-and-landmark-snapshots|Risk-set construction]] is the next step; the final target cannot be inferred from a binary label alone.')],
    '''inspection_episodes = [
    {"vehicle": "fleet-47", "inspection_day": 24, "event_day": 81, "last_seen_day": 92},
    {"vehicle": "fleet-62", "inspection_day": 31, "event_day": None, "last_seen_day": 102},
    {"vehicle": "fleet-83", "inspection_day": 39, "event_day": 67, "last_seen_day": 86},
]

def survival_targets(episodes):
    targets = []
    for episode in episodes:
        origin = episode["inspection_day"]
        event = episode["event_day"]
        observed = event is not None and event <= episode["last_seen_day"]
        end = event if observed else episode["last_seen_day"]
        if end < origin:
            raise ValueError("follow-up ends before inspection")
        targets.append((episode["vehicle"], end - origin, observed))
    return targets

assert survival_targets(inspection_episodes) == [
    ("fleet-47", 57, True), ("fleet-62", 71, False), ("fleet-83", 28, True)]''',
    'Building N targets costs O(N) time and O(N) output storage. The harder expense is reliable event reconciliation and censor-reason auditing. A binary classification shortcut can seem cheaper, but it discards varying follow-up and may train on immature negatives.',
    ['Do not replace a censored time with an event time.', 'Do not mix purchase-date and inspection-date origins.', 'Do not include post-inspection repair fields among baseline predictors.'],
    ['machine-learning/survival-risk-set-and-landmark-snapshots','machine-learning/time-varying-survival-features','machine-learning/survival-model-evaluation-at-horizons','machine-learning/fleet-survival-release-project'])


add('survival-risk-set-and-landmark-snapshots',
    'Survival risk sets and landmark snapshots',
    'A risk set contains only units still eligible just before an event time; a landmark prediction resets the question for units that remain event-free at that landmark.', [
    ('Keep the event order explicit', 'At day 28 after inspection, a vehicle that already had a replacement is no longer at risk for its first replacement. A vehicle censored at day 19 is also absent because follow-up ended. A vehicle censored at day 43 was known to remain event-free through day 28 and belongs in the risk set. This distinction drives survival likelihoods and evaluation denominators.'),
    ('Treat delayed entry separately', 'A vehicle may join the fleet monitoring feed 12 days after inspection. If it was eligible but invisible before entry, placing it in earlier risk sets grants unobserved event-free time. Record entry age and include the vehicle only after entry. Delayed entry is not the same as right-censoring at the end. [[data-science/cohort-entry-and-survivorship-bias|Entry bias]] can distort comparisons.'),
    ('Build landmark datasets for fresh decisions', 'At day 30, operations may ask for risk over the next 45 days using the current voltage reading. Include only vehicles still event-free and observed at day 30; use readings available by day 30. The target begins at the landmark, not the original inspection. A new landmark creates a new prediction episode and requires grouped splitting by vehicle.'),
    ('State endpoint conventions', 'If an event is recorded at exactly day 30, decide whether it belongs before or after a day-30 snapshot. Use one consistent half-open interval convention in data creation and model evaluation. The code uses entry <= t and exit >= t for a just-before-t risk set; events at t are included until that event is processed.'),
    ('Check support by slice', 'A far-future landmark may retain only well-maintained vehicles, changing the population. Report risk-set size by depot and vehicle model at each candidate horizon. [[machine-learning/survival-model-evaluation-at-horizons|Horizon evaluation]] should not hide a tiny late risk set.')],
    '''follow_up = [
    {"vehicle": "fleet-47", "entry": 0, "exit": 57, "event": True},
    {"vehicle": "fleet-62", "entry": 12, "exit": 71, "event": False},
    {"vehicle": "fleet-83", "entry": 0, "exit": 28, "event": True},
    {"vehicle": "fleet-94", "entry": 0, "exit": 19, "event": False},
]

def at_risk_just_before(records, day):
    return [row["vehicle"] for row in records
            if row["entry"] <= day <= row["exit"]]

assert at_risk_just_before(follow_up, 28) == [
    "fleet-47", "fleet-62", "fleet-83"]
assert at_risk_just_before(follow_up, 58) == ["fleet-62"]''',
    'A direct scan costs O(N) time per event or landmark and O(N) output memory. Sorting entry and exit times supports faster repeated queries; full model fitting may need event-time risk summaries. Landmark tables increase row count and require vehicle-level grouping to keep evaluation independent.',
    ['Do not place a vehicle into risk sets before it entered observation.', 'Do not let a prior event remain at risk for its first occurrence.', 'Do not treat a landmark dataset as independent rows during splitting.'],
    ['machine-learning/time-to-event-target-and-censor-contract','machine-learning/time-varying-survival-features','machine-learning/survival-model-evaluation-at-horizons','machine-learning/fleet-survival-release-project'])


add('time-varying-survival-features',
    'Time-varying survival features without future leakage',
    'Changing covariates belong to intervals where their values were already known; copying the latest value backward creates a future-information leak.', [
    ('Choose a clock for each measurement', 'Fleet voltage is measured after inspections and maintenance visits. A reading taken on day 41 can inform predictions made after day 41, not the day-24 inspection risk. Record observation and availability timestamps, since uploads may arrive after measurements. Use the time when the service could have used the value.'),
    ('Represent stable intervals', 'A time-varying model can split a vehicle episode into start-stop intervals. Each interval carries the value known before its endpoint; status is true only on the interval ending with the event. Intervals cannot overlap or extend beyond the observed exit. [[machine-learning/survival-risk-set-and-landmark-snapshots|Risk sets]] then use the current value at each event time.'),
    ('Separate interventions from predictors', 'A new battery-warning flag may cause maintenance that prevents replacement. Treating that flag as an ordinary predictor can entangle prediction with an intervention policy. If the aim is counterfactual risk under no action, a standard observational survival model is not enough. State the actual estimand: risk under the current operational policy.'),
    ('Avoid backfill artifacts', 'A warehouse may overwrite a voltage field with its latest value. Historical snapshots must come from an append-only log or versioned table. Forward filling is acceptable only from earlier available readings and with a maximum age rule; never fill backward from a later inspection. [[machine-learning/prediction-time-feature-availability|Availability auditing]] applies at interval level.'),
    ('Test the serving snapshot', 'Replay a past inspection and a day-45 landmark from timestamped records. Confirm that every emitted feature existed at that decision time. Compare a baseline-only model to a landmark update model on future vehicles, using paired horizons and the same censoring policy.')],
    '''readings = [
    {"available_day": 24, "voltage": 12.6},
    {"available_day": 41, "voltage": 12.2},
    {"available_day": 58, "voltage": 11.9},
]

def last_available_voltage(observations, decision_day):
    eligible = [reading for reading in observations
                if reading["available_day"] <= decision_day]
    return max(eligible, key=lambda reading: reading["available_day"])["voltage"] if eligible else None

assert last_available_voltage(readings, 30) == 12.6
assert last_available_voltage(readings, 45) == 12.2
assert last_available_voltage(readings, 20) is None''',
    'The simple snapshot scan is O(M) per request over M readings; sorted, indexed histories support O(log M) lookup. Interval expansion adds storage proportional to measurement changes. Event-time fitting may be substantially more expensive than a baseline-only model, so measure whether updated predictions improve decisions.',
    ['Do not copy the final voltage reading into earlier intervals.', 'Do not confuse measurement timestamp with availability timestamp.', 'Do not interpret policy-affected risk as untreated failure risk.'],
    ['machine-learning/time-to-event-target-and-censor-contract','machine-learning/survival-risk-set-and-landmark-snapshots','machine-learning/survival-model-evaluation-at-horizons','machine-learning/fleet-survival-release-project'])


add('survival-model-evaluation-at-horizons',
    'Survival-model evaluation at supported horizons',
    'Discrimination, calibration and decision value must be measured at horizons with enough observed follow-up; ordinary binary metrics cannot treat all censored cases as negatives.', [
    ('Name the output', 'An operations dashboard may need the probability of battery replacement within 45 days of inspection. A hazard ratio is not this probability, and a risk ranking alone does not supply a calibrated 45-day forecast. Convert the fitted model to a survival or cumulative-risk estimate under its assumptions, then validate at the specified horizon.'),
    ('Handle unknown horizon outcomes', 'For a 45-day test, a vehicle replaced on day 23 is an event, and one observed event-free through day 45 is a known nonevent. A vehicle last seen event-free on day 29 has unknown day-45 status. Dropping it naively may bias results if censoring is selective. Use a justified censoring-aware estimator and test support before claiming calibration. [[data-science/ipcw-brier-score-for-survival-predictions|Censor-weighted Brier scoring]] gives one approach.'),
    ('Separate ranking from probabilities', 'Concordance summarizes ordering among comparable pairs, while a horizon Brier score and calibration bins assess predicted probabilities. A model may rank older batteries correctly yet consistently overstate 45-day failures. Report both aspects, plus event counts and uncertainty by depot. [[data-science/fixed-horizon-survival-prediction-calibration|Fixed-horizon calibration]] expands the diagnostic.'),
    ('Inspect the censor process', 'Estimate observation survival by route, depot and maintenance status. Very large inverse-censor weights signal weak support; cap the claimed horizon or gather more follow-up rather than trusting a high-variance score. Do not tune the censor model or decision threshold on the final test.'),
    ('Tie metrics to action', 'If only 26 vehicle inspections can be prioritized weekly, compare the number of replacements captured in the highest-risk eligible cohort, with a clear handling rule for censored outcomes. The dashboard should show uncertainty and avoid pretending that a thin 180-day tail is as reliable as the 45-day estimate.')],
    '''episodes = [
    {"vehicle": "fleet-47", "follow_up": 57, "event": True, "risk_45": 0.24},
    {"vehicle": "fleet-62", "follow_up": 71, "event": False, "risk_45": 0.08},
    {"vehicle": "fleet-83", "follow_up": 28, "event": True, "risk_45": 0.43},
    {"vehicle": "fleet-94", "follow_up": 19, "event": False, "risk_45": 0.12},
]

def known_horizon_status(record, horizon):
    if record["event"] and record["follow_up"] <= horizon:
        return 1
    if record["follow_up"] >= horizon:
        return 0
    return None

statuses = {row["vehicle"]: known_horizon_status(row, 45) for row in episodes}
assert statuses == {"fleet-47": 0, "fleet-62": 0,
                    "fleet-83": 1, "fleet-94": None}''',
    'Assigning known horizon status costs O(N) time and O(N) output storage. The code intentionally leaves early-censored outcomes unknown; it is not a censoring-adjusted score. Censoring estimation, resampling for uncertainty and full survival-curve prediction add compute and data requirements.',
    ['Do not count early-censored cases as day-45 nonevents.', 'Do not equate a hazard ratio with an absolute failure probability.', 'Do not report a distant-horizon score without at-risk and censor support.'],
    ['machine-learning/time-to-event-target-and-censor-contract','machine-learning/survival-risk-set-and-landmark-snapshots','machine-learning/time-varying-survival-features','machine-learning/fleet-survival-release-project'])


add('competing-event-and-service-policy-review',
    'Competing events and service-policy review',
    'A vehicle sale or permanent withdrawal can prevent the target replacement; treating it as ordinary independent censoring can misstate the replacement probability.', [
    ('Classify end states', 'From an inspection, a vehicle may receive battery replacement, be sold, leave the fleet for another reason, or remain under observation. Sale prevents a fleet replacement under the current policy; it is a competing event, not a hidden future replacement. Distinguish it from an administrative export cutoff. [[data-science/competing-risks-and-resolution-incidence|Competing-risk incidence]] supplies the probability target.'),
    ('Match probability to the decision', 'A mechanic deciding whether to pre-order parts needs the chance of replacement while the vehicle remains in the fleet. A hypothetical failure risk in a world where no vehicle is sold is a different question. The model output label must say which probability it estimates; otherwise two correct methods can appear to disagree.'),
    ('Track policy changes', 'Preventive maintenance may replace batteries earlier or avoid emergency replacement. If a new policy begins midway through the dataset, event incidence changes because actions changed, not necessarily because battery condition improved. Evaluate by calendar period and policy version. A risk model trained on old policy may not forecast the new one.'),
    ('Do not collapse event types', 'A generic “closed episode” label merges replacement and sale, teaching the model to predict fleet turnover. The code retains explicit end states and computes crude counts; those counts are not cumulative-incidence estimates because follow-up differs. [[machine-learning/survival-model-evaluation-at-horizons|Censor-aware evaluation]] is still required.'),
    ('Write a release gate', 'Set acceptable calibration for replacement incidence at a supported horizon and track sale incidence as a separate context measure. Hold deployment if a depot’s sale process is not recorded or if the maintenance policy changed without a compatible validation window. [[machine-learning/fleet-survival-release-project|The release project]] joins these checks.')],
    '''vehicle_end_states = [
    {"vehicle": "fleet-47", "day": 57, "state": "replacement"},
    {"vehicle": "fleet-62", "day": 71, "state": "administrative_cutoff"},
    {"vehicle": "fleet-83", "day": 28, "state": "sale"},
    {"vehicle": "fleet-94", "day": 64, "state": "replacement"},
]

def end_state_counts(records):
    allowed = {"replacement", "sale", "administrative_cutoff"}
    counts = {state: 0 for state in allowed}
    for record in records:
        if record["state"] not in allowed:
            raise ValueError("unclassified end state")
        counts[record["state"]] += 1
    return counts

assert end_state_counts(vehicle_end_states) == {
    "replacement": 2, "sale": 1, "administrative_cutoff": 1}''',
    'Classifying N episode endpoints costs O(N) time and O(1) counters for a fixed event vocabulary. Estimating cause-specific or cumulative-incidence curves needs event-time risk sets and sufficient follow-up. Policy-stratified validation reduces sample size, so show support before drawing conclusions.',
    ['Do not code sale as a battery replacement.', 'Do not interpret crude event fractions as horizon probabilities.', 'Do not ignore preventive-maintenance policy changes in model validation.'],
    ['machine-learning/time-to-event-target-and-censor-contract','machine-learning/survival-model-evaluation-at-horizons','machine-learning/fleet-survival-release-project','data-science/competing-risk-prediction-calibration-and-brier-score'])


add('fleet-survival-release-project',
    'Project: release review for fleet battery-replacement timing',
    'A time-to-event release decision joins event and censor contracts, valid risk sets, horizon support, competing events and operational capacity.', [
    ('Freeze the forecast', 'The fleet team needs 45-day replacement probability from each scheduled inspection. Keep inspection-day features available then, define confirmed replacement, sale, administrative cutoff and repeat episodes, and reserve later vehicle inspections for final evaluation. Entire vehicles stay in one split. [[machine-learning/time-to-event-target-and-censor-contract|The target contract]] is the first release artifact.'),
    ('Train comparable candidates', 'Start with a simple age-and-voltage survival baseline. Compare a model with additional historical service features under the same split. If voltage is updated after inspection, evaluate it only in a separate landmark model with start-stop intervals and a new decision clock. [[machine-learning/survival-risk-set-and-landmark-snapshots|Risk sets]] and [[machine-learning/time-varying-survival-features|time-varying records]] must remain auditable.'),
    ('Evaluate the supported horizon', 'Report 45-day calibration, ranking, observed event count, censoring pattern and replacement incidence by depot and vehicle model. Do not score early-censored cases as negatives. Check whether enough vehicles are observed through day 45 for stable weighting, then assess the highest-risk 26 inspections against weekly service capacity. [[machine-learning/survival-model-evaluation-at-horizons|Horizon evaluation]] defines the metrics.'),
    ('Review competing outcomes', 'Vehicles sold before 45 days cannot later receive a fleet replacement under the current policy. Measure their incidence separately and label the forecast as replacement under existing service and sale policy. Reassess after a policy change. [[machine-learning/competing-event-and-service-policy-review|Competing events]] are a release concern, not a footnote.'),
    ('Hold on unsupported claims', 'The sample packet below rejects an otherwise plausible model because only 19 vehicles are still observed at the chosen 180-day report horizon. Remove that unsupported long-horizon claim, rerun the fixed 45-day gate, and keep the prior maintenance schedule available for rollback. No model score can repair missing follow-up.')],
    '''release_packet = {
    "target_contract_locked": True,
    "future_feature_leaks": 0,
    "day_45_risk_set": 234,
    "minimum_day_45_risk_set": 90,
    "day_180_risk_set": 19,
    "minimum_day_180_risk_set": 65,
    "reports_day_180": True,
    "sale_recording_complete": True,
    "weekly_review_volume": 24,
    "weekly_review_capacity": 26,
}

def review_fleet_release(packet):
    blockers = []
    if not packet["target_contract_locked"] or packet["future_feature_leaks"]:
        blockers.append("target or feature contract failed")
    if packet["day_45_risk_set"] < packet["minimum_day_45_risk_set"]:
        blockers.append("45-day support insufficient")
    if packet["reports_day_180"] and packet["day_180_risk_set"] < packet["minimum_day_180_risk_set"]:
        blockers.append("180-day support insufficient")
    if not packet["sale_recording_complete"]:
        blockers.append("competing sale events unresolved")
    if packet["weekly_review_volume"] > packet["weekly_review_capacity"]:
        blockers.append("review capacity exceeded")
    return {"release": not blockers, "blockers": blockers}

decision = review_fleet_release(release_packet)
assert decision == {"release": False, "blockers": ["180-day support insufficient"]}''',
    'The packet check is O(1), but obtaining its evidence requires dated event reconciliation, risk-set construction, model fitting, censor-aware horizon scores and depot-level review. The extra 180-day forecast cannot be justified by a cheap extrapolation when the supported population is too small.',
    ['Do not approve a longer horizon from a short-horizon result.', 'Do not claim sale is independent censoring without review.', 'Do not ignore the weekly service capacity when setting a risk threshold.'],
    ['machine-learning/time-to-event-target-and-censor-contract','machine-learning/survival-risk-set-and-landmark-snapshots','machine-learning/time-varying-survival-features','machine-learning/survival-model-evaluation-at-horizons','machine-learning/competing-event-and-service-policy-review','data-science/competing-risk-prediction-calibration-and-brier-score'])


publish_batch(
    lessons,
    module_title='Time-to-event machine learning and fleet decisions',
    module_summary='Define censor-aware targets, current risk sets and supported horizon decisions for operational survival models.',
    project_heading='Fleet battery timing release project',
    crosslinks=[
        ('machine-learning/prediction-time-feature-availability', 'machine-learning/time-to-event-target-and-censor-contract'),
        ('machine-learning/group-and-time-validation', 'machine-learning/survival-risk-set-and-landmark-snapshots'),
        ('machine-learning/probability-calibration', 'machine-learning/survival-model-evaluation-at-horizons'),
        ('data-science/right-censoring-and-time-to-event', 'machine-learning/time-to-event-target-and-censor-contract'),
        ('data-science/competing-risks-and-resolution-incidence', 'machine-learning/competing-event-and-service-policy-review'),
    ],
    sort_start=6600,
)
