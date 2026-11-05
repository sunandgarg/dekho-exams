"""Publish original lessons on categorical flows, spectrograms, and raincloud plots."""
from data_visualization_batch import publish

prefix = "data-visualization/"
lessons = [
    {
        "slug": "alluvial-categories-fixed-cohort-and-observation-gaps",
        "title": "Alluvial diagrams: follow one cohort through categorical stages",
        "summary": "Build ribbons from stable record identities, preserve the stage total, and distinguish an unobserved state from a measured exit.",
        "sections": [
            ("Start with the same population on every axis", "An alluvial diagram follows records through a sequence of categorical observations. Each vertical axis is a stage or attribute; a ribbon groups records that share adjacent categories. The picture answers a different question from a general [[data-visualization/sankey-flow-conservation-and-unobserved-exits|Sankey flow]]: which members of a fixed cohort changed category, and where did their recorded paths split? Establish the cohort before counting anything. If the first axis includes all accounts opened in April but the third includes every active account in June, the ribbon widths no longer describe transitions within one population. New entrants need a separate cohort or an explicit entrant category. Each record needs a stable identifier, a stage definition, and at most one category at a stage. A row count without identity cannot reveal whether the same seven accounts moved through the diagram or seven different accounts were sampled each time. [[data-visualization/aggregation-grain-and-denominator|Grain and denominators]] are the first validation gate."),
            ("Keep unobserved records in the ledger", "A missing stage value is not automatically churn, failure, or inactivity. It may reflect a late data feed, an ineligible record, or a lost join. The worked contract keeps an explicit Not observed category so every axis and adjacent ribbon set still sums to the original cohort size. Analysts can then separate recorded churn from incomplete measurement. If the business meaning of absence is genuinely an exit, encode that as a distinct recorded event with a timestamp and an eligibility rule. Do not silently turn null into churn. Count each adjacent pair from the same record ledger; independently aggregated stage totals cannot reconstruct who crossed between categories. For a large diagram, group rare categories by a declared rule and keep an exact transition table. [[data-visualization/cohort-retention-heatmaps-maturity-denominators-and-return-events|Cohort retention]], [[data-visualization/missingness-matrices-record-order-patterns-and-co-missing-fields|missingness]] and [[data-visualization/linked-filters-cohort-denominators-and-selection-state|linked filters]] show how the population can drift."),
            ("Order categories without inventing movement", "Ribbon geometry depends on vertical category order. If each axis is reordered by its latest count, unchanged paths can cross even when the underlying records have not moved. Choose a domain order for each stage, version it, and hold it across comparable panels and exports. Keep a stable color meaning: color by the initial category when the question is origin, or by the final outcome when the question is destination. A gradient that changes meaning halfway through the diagram makes the path hard to decode. The ribbon width should represent count on a shared scale, while the hover text and adjacent table expose the exact count and denominator. Stage-specific percentages can be useful, but label their denominator; a ribbon of three out of four active trials is not the same quantity as three out of seven original accounts. [[data-visualization/stacked-bars-composition-and-changing-denominators|Stacked bars]] are easier when only stage composition matters."),
            ("Design for inspection, not just spectacle", "Crossing ribbons are expensive to trace by eye. Highlight a selected origin or destination, dim unrelated paths, and include a keyboard-accessible transition table with stage pair, source, destination and count. Do not make users identify a one-record path from a hairline ribbon. If there are many stages, provide a small-multiple view of adjacent pairs, then let a reader inspect one segment at a time. A stage with a newly introduced category should disclose the schema change; otherwise its ribbon can masquerade as behavioral movement. Preserve the filter state and cohort key in exported data. When identity cannot be linked across stages, the correct output is a sequence of separate category summaries, not an invented alluvial path. [[data-visualization/interactive-chart-keyboard-focus-and-data-table-contract|Keyboard access]], [[data-visualization/chart-export-manifest-data-and-render-version|export manifests]] and [[data-visualization/chord-diagrams-directed-flows-self-loops-and-sector-totals|chord diagrams]] provide nearby design choices."),
        ],
        "code": '''from collections import Counter

def build_account_alluvium(cohort_ids, stages, observations):
    if (not cohort_ids or len(set(cohort_ids)) != len(cohort_ids) or
            any(not isinstance(account_id, str) or not account_id.strip()
                for account_id in cohort_ids)):
        raise ValueError("cohort IDs must be unique nonempty strings")
    if (len(stages) < 2 or len(set(stages)) != len(stages) or
            any(not isinstance(stage, str) or not stage.strip() for stage in stages)):
        raise ValueError("at least two unique stages are required")
    cohort, stage_set = set(cohort_ids), set(stages)
    state_by_account_stage = {}
    for account_id, stage, state in observations:
        key = (account_id, stage)
        if (account_id not in cohort or stage not in stage_set or
                not isinstance(state, str) or not state.strip() or
                state == "Not observed" or key in state_by_account_stage):
            raise ValueError(f"invalid or duplicate observation: {key}")
        state_by_account_stage[key] = state

    def state_at(account_id, stage):
        return state_by_account_stage.get((account_id, stage), "Not observed")

    stage_counts = [Counter(state_at(account_id, stage) for account_id in cohort_ids)
                    for stage in stages]
    ribbons = [Counter((state_at(account_id, left), state_at(account_id, right))
                       for account_id in cohort_ids)
               for left, right in zip(stages, stages[1:])]
    assert all(sum(counts.values()) == len(cohort_ids) for counts in stage_counts)
    assert all(sum(counts.values()) == len(cohort_ids) for counts in ribbons)
    return stage_counts, ribbons

accounts = [f"AC-{number}" for number in range(41, 48)]
stages = ["intake", "trial", "renewal"]
observations = [
    ("AC-41", "intake", "direct"), ("AC-42", "intake", "direct"),
    ("AC-43", "intake", "referral"), ("AC-44", "intake", "referral"),
    ("AC-45", "intake", "partner"), ("AC-46", "intake", "partner"),
    ("AC-47", "intake", "direct"),
    ("AC-41", "trial", "active"), ("AC-42", "trial", "active"),
    ("AC-43", "trial", "inactive"), ("AC-44", "trial", "active"),
    ("AC-45", "trial", "active"), ("AC-46", "trial", "inactive"),
    ("AC-41", "renewal", "renewed"), ("AC-42", "renewal", "churned"),
    ("AC-43", "renewal", "churned"), ("AC-44", "renewal", "renewed"),
    ("AC-45", "renewal", "renewed"),
]
stage_counts, ribbons = build_account_alluvium(accounts, stages, observations)
assert stage_counts[2]["Not observed"] == 2
assert ribbons[1][("active", "renewed")] == 3
assert ribbons[1][("inactive", "Not observed")] == 1''',
        "cost": "Let C be cohort size, S the number of stages, and R the number of supplied observations. Validating the observations and building the stage and adjacent-pair ledgers takes O(R + CS) time; storing the input lookup and aggregate counts takes O(R + CS) space in the worst case. In the worked seven-account cohort, three active trials become recorded renewals, one inactive trial has no renewal observation, and two accounts lack a renewal observation in total. Both adjacent ribbon sets still sum to seven. The code prepares counts; a renderer must apply a documented category order and a fixed width scale. Avoid drawing every record as its own ribbon when C is large: aggregate equal paths and retain the exact ledger for inspection.",
        "mistakes": ["Building each stage from a different population and labeling the ribbons as cohort transitions.", "Inferring a person's path from stage-level totals without stable record identity.", "Treating a missing observation as a recorded exit or churn event.", "Changing category order or color meaning between comparison panels.", "Displaying percentages without naming whether the denominator is the original cohort or a stage subset."],
        "drill": "Take a fixed cohort of 47 accounts observed at onboarding, first use and renewal. Verify one category per account per stage, preserve missing observations explicitly, reconcile every stage and ribbon set to 47, and publish a tabular list of the transitions that remain after rare categories are grouped.",
        "related": [prefix + "sankey-flow-conservation-and-unobserved-exits", prefix + "cohort-retention-heatmaps-maturity-denominators-and-return-events", prefix + "linked-filters-cohort-denominators-and-selection-state", prefix + "interactive-chart-keyboard-focus-and-data-table-contract"],
    },
    {
        "slug": "spectrograms-window-hop-frequency-resolution-and-decibel-domain",
        "title": "Spectrograms: make time, frequency and color scales defensible",
        "summary": "Turn sampled signals into time–frequency cells with explicit window and hop lengths, a real amplitude reference, and an honest display floor.",
        "sections": [
            ("Every cell is a windowed estimate", "A spectrogram shows how a sampled signal's frequency content changes over time. A row is a frequency bin, a column is a window position, and color encodes a defined measure such as amplitude or power. It is not a photograph of instantaneous frequency. Each column summarizes a finite stretch of samples; an abrupt event may influence several overlapping columns. Publish the sample rate, window length, hop length, window function, frequency units and color quantity. A signal sampled at 64 samples per second has a 32 hertz Nyquist frequency; frequencies above it cannot be uniquely represented without an anti-aliasing policy upstream. A 16-sample window lasts 0.25 seconds and places Fourier bins four hertz apart. Those are properties of the measurement contract, not choices to hide in rendering code. [[data-visualization/time-series-gaps-calendars-and-provisional-periods|Time-series gaps]] and [[data-visualization/heatmap-missing-cells-and-color-domain|heatmap domains]] handle the adjacent display risks."),
            ("Choose window and hop for the question", "A longer window separates nearby stable frequencies more finely, but it smears changes across more time. A shorter window localizes an event better while merging nearby frequencies. The hop controls how often the estimate is placed on the time axis; it does not create new information between samples. Overlap can make a display smoother, yet adjacent columns then share data and are not independent observations. A tapered window reduces the sharp edge introduced by slicing the signal, at the cost of spreading a bin-centered tone into neighboring bins. The worked example uses a Hann window, a 16-sample frame and an eight-sample hop. For a long recording, use a tested FFT implementation, cache only the visible range, and preserve the original sampling metadata. [[data-visualization/large-series-level-of-detail-and-extrema|Level of detail]] matters before millions of cells reach a browser."),
            ("Label the decibel reference and floor", "Decibels express a ratio, so a label that says dB without a reference is incomplete. The code computes an amplitude ratio against a reference amplitude of one and displays 20 times its base-ten logarithm. This is not calibrated sound-pressure level. A zero-amplitude bin would be negative infinity; the chosen minus-80-decibel floor keeps the display finite, and the legend must say that darker cells may be at or below that floor. Use the same color limits when comparing recordings. Rescaling each panel to its own maximum can make a quiet background resemble a loud event. Power or power spectral density requires a different normalization and should not be relabeled as amplitude. A log-frequency axis is another independent choice: it changes spacing on the vertical axis, not the contents of a Fourier bin. [[data-visualization/scale-baseline-and-axis-integrity|Axis rules]] and [[data-visualization/accessible-color-and-text-alternatives|text alternatives]] prevent an attractive display from making an unsupported comparison."),
            ("Do not paint missing samples as silence", "A telemetry dropout has no measured amplitude. Replacing it with zeros creates a vertical dark stripe and can inject a false transient at the gap boundary. Mark the affected windows as unavailable, or process only continuous spans and leave a visible break. Similarly, a microphone gain change or sensor recalibration can shift every color without changing the underlying event; annotate those changes and keep calibration metadata with the export. If a narrow bright line appears at one fixed frequency, check for machinery, power-line interference, sampling artifacts and window leakage before assigning a cause. For speech or music, the display can help locate intervals for listening, but color alone does not prove what produced a sound. Preserve the raw signal segment, transform parameters and render version in a [[data-visualization/chart-export-manifest-data-and-render-version|chart export manifest]]."),
        ],
        "code": '''from math import cos, hypot, isfinite, log10, pi, sin

def amplitude_spectrogram(samples, sample_rate, window_length, hop, floor_db=-80):
    values = list(samples)
    if (isinstance(sample_rate, bool) or not isinstance(sample_rate, (int, float)) or
            not isfinite(sample_rate) or sample_rate <= 0 or
            not isinstance(window_length, int) or isinstance(window_length, bool) or
            window_length < 4 or window_length % 2 or
            not isinstance(hop, int) or isinstance(hop, bool) or
            not 1 <= hop <= window_length or
            not isfinite(floor_db) or floor_db >= 0 or len(values) < window_length or
            any(isinstance(value, bool) or not isinstance(value, (int, float))
                or not isfinite(value) for value in values)):
        raise ValueError("invalid samples or transform settings")
    taper = [0.5 - 0.5 * cos(2 * pi * offset / (window_length - 1))
             for offset in range(window_length)]
    coherent_gain = sum(taper)
    frequencies_hz = [bin_index * sample_rate / window_length
                      for bin_index in range(window_length // 2 + 1)]
    amplitude_floor = 10 ** (floor_db / 20)
    columns = []
    for start in range(0, len(values) - window_length + 1, hop):
        frame = [values[start + offset] * taper[offset]
                 for offset in range(window_length)]
        levels_db = []
        for bin_index in range(len(frequencies_hz)):
            phase_step = 2 * pi * bin_index / window_length
            real = sum(value * cos(phase_step * offset)
                       for offset, value in enumerate(frame))
            imaginary = -sum(value * sin(phase_step * offset)
                             for offset, value in enumerate(frame))
            amplitude = hypot(real, imaginary) / coherent_gain
            if 0 < bin_index < window_length // 2:
                amplitude *= 2
            levels_db.append(20 * log10(max(amplitude, amplitude_floor)))
        center_seconds = (start + (window_length - 1) / 2) / sample_rate
        columns.append((center_seconds, levels_db))
    return frequencies_hz, columns

sample_rate = 64
signal = [sin(2 * pi * (8 if index < 32 else 16) * index / sample_rate)
          for index in range(64)]
frequencies, columns = amplitude_spectrogram(signal, sample_rate, 16, 8)
def strongest_frequency(levels):
    return frequencies[max(range(len(levels)), key=levels.__getitem__)]
assert strongest_frequency(columns[0][1]) == 8
assert strongest_frequency(columns[-1][1]) == 16
assert len(columns) == 7 and frequencies[-1] == 32''',
        "cost": "With F windows of W samples, this transparent direct Fourier transform costs O(FW²) time and O(FW) space for a complete output matrix. Production FFT implementations reduce transform work to roughly O(FW log W), while a streamed renderer can bound memory to the visible columns. The sample uses 64 samples per second, 16 samples per window and an eight-sample hop: seven columns, four-hertz bin spacing, a 32-hertz Nyquist limit and one-half overlap. Its first complete window is strongest at eight hertz, while the final complete window is strongest at sixteen hertz. The intermediate windows mix the two segments. The decibel values are relative amplitudes, with a minus-80-decibel display floor; they are not a calibrated loudness measurement.",
        "mistakes": ["Calling adjacent overlapping windows independent measurements.", "Using a larger hop and claiming it improves the underlying time resolution.", "Labeling relative amplitude decibels as calibrated sound-pressure levels.", "Choosing a new color minimum and maximum for every panel that must be compared.", "Replacing missing samples with zeros and reading the resulting stripe as silence."],
        "drill": "Analyze a 47-second machine recording with a declared sample rate. Freeze window, hop, taper, reference and color bounds before comparing it with another run. Mark any sample gaps, inspect whether a detected stripe survives a different window length, and export the transform settings beside the cells.",
        "related": [prefix + "heatmap-missing-cells-and-color-domain", prefix + "time-series-gaps-calendars-and-provisional-periods", prefix + "large-series-level-of-detail-and-extrema", prefix + "chart-export-manifest-data-and-render-version"],
    },
    {
        "slug": "raincloud-plots-fixed-bandwidth-raw-points-and-unequal-groups",
        "title": "Raincloud plots: show the estimate, summary and records together",
        "summary": "Combine a density silhouette, quartile summary and stable raw points without hiding unequal group sizes or bandwidth choices.",
        "sections": [
            ("Three layers answer three questions", "A raincloud plot places a distribution estimate, a compact summary and individual observations beside one another for each group. The density shape helps locate concentrations, the quartiles orient a comparison, and raw points reveal outliers, ties and sample size. None of the layers should be allowed to contradict another through a hidden filter. Use the same eligible records for all three, then display the count near each group. For service latency, a broad-looking density may come from seven observations while a narrow-looking one may come from hundreds; if both are normalized to area one, shape width is not a record count. Keep a shared value axis and state whether the density is normalized within each group or scaled to count. A simple [[data-visualization/box-violin-and-kde-bandwidth-for-group-comparisons|box or violin plot]] may be clearer when there are many groups. [[data-visualization/beeswarm-plots-collision-spacing-and-sample-count|Beeswarm points]] are a better raw layer when exact overlaps matter."),
            ("Freeze smoothing and value bounds", "The cloud is a model of a distribution, not a trace of every observation. A Gaussian kernel density estimate spreads each record over nearby values according to a bandwidth. Too little smoothing turns each value into its own bump; too much erases shoulders or separated clusters. For a comparison, use one declared bandwidth in the measured unit and one common grid. If groups are measured on different units, convert them before plotting or keep separate panels. The example below uses a fixed bandwidth of two minutes and a grid spanning every observed value plus three bandwidths on each side. That avoids trimming the visible tails differently by group. It also keeps the half-violin widths as within-group density, so their maximum heights should not be read as a sample-size comparison. [[data-visualization/unequal-bin-histograms-density-area-and-boundary-policy|Histogram density]] offers another check on smoothing."),
            ("Keep raw points stable and quartile policy explicit", "A little horizontal jitter separates identical or nearly identical values, but jitter must not alter the measured axis. The code derives a stable display offset from each record identifier, so refreshing a dashboard does not make the same observation jump to a random place. It does not guarantee that all points are collision-free; densely repeated values may still need a beeswarm algorithm or a count label. The quartiles use one named calculation policy, and the same policy must be used for every group and exported summary. A whisker rule should also be named if whiskers are drawn. The worked ledger omits them rather than letting a plotting library silently choose. When records are paired across groups, a raincloud can conceal that relationship; a connected paired display is more appropriate for the primary comparison. [[data-visualization/paired-change-slope-and-dumbbell-charts|Paired change charts]] preserve identity."),
            ("Choose a view that survives small screens", "A cloud, box and points can become three cramped marks on a phone. Keep the value axis labeled, leave room for group names, and offer a table with count, median, quartiles and every raw value when feasible. A screen reader should not announce a hundred decorative cloud coordinates; it needs the group summary and a path to the underlying records. If a small group contains only a handful of observations, the smoothed cloud can imply more certainty than the data warrant. Show the points and summary first, and either omit the density or label it as exploratory. If a record disappears under a filter, recompute all three layers from the same filtered population. [[data-visualization/uncertainty-and-small-sample-display|Small-sample display]], [[data-visualization/accessible-color-and-text-alternatives|accessible alternatives]] and [[data-visualization/small-multiples-shared-scales-and-facet-order|shared facets]] help keep the comparison honest."),
        ],
        "code": '''from hashlib import blake2s
from math import exp, isfinite, pi, sqrt
from statistics import median, quantiles

def prepare_latency_raincloud(groups, bandwidth_minutes, grid_size=41):
    if (not groups or not isinstance(bandwidth_minutes, (int, float)) or
            isinstance(bandwidth_minutes, bool) or not isfinite(bandwidth_minutes) or
            bandwidth_minutes <= 0 or not isinstance(grid_size, int) or
            isinstance(grid_size, bool) or grid_size < 3):
        raise ValueError("invalid groups, bandwidth or grid size")
    all_minutes = []
    for group_name, records in groups.items():
        if not isinstance(group_name, str) or not group_name.strip() or len(records) < 4:
            raise ValueError("each named group needs at least four records")
        record_ids = [record_id for record_id, _ in records]
        if (len(set(record_ids)) != len(record_ids) or
                any(not isinstance(record_id, str) or not record_id.strip()
                    for record_id in record_ids)):
            raise ValueError("record IDs must be unique within each group")
        for _, minutes in records:
            if (not isinstance(minutes, (int, float)) or isinstance(minutes, bool) or
                    not isfinite(minutes) or minutes < 0):
                raise ValueError("latencies must be finite nonnegative minutes")
            all_minutes.append(minutes)
    lower = min(all_minutes) - 3 * bandwidth_minutes
    upper = max(all_minutes) + 3 * bandwidth_minutes
    grid = [lower + (upper - lower) * index / (grid_size - 1)
            for index in range(grid_size)]
    prepared = {}
    for group_name, records in groups.items():
        minutes = sorted(value for _, value in records)
        first_quartile, _, third_quartile = quantiles(minutes, n=4, method="inclusive")
        density = [sum(exp(-0.5 * ((position - value) / bandwidth_minutes) ** 2)
                       for value in minutes) /
                   (len(minutes) * bandwidth_minutes * sqrt(2 * pi))
                   for position in grid]
        points = []
        for record_id, value in records:
            digest = blake2s(record_id.encode(), digest_size=4).digest()
            display_offset = (int.from_bytes(digest, "big") / 2**32 - 0.5) * 0.2
            points.append((record_id, value, display_offset))
        prepared[group_name] = {"count": len(minutes), "median": median(minutes),
                                "quartiles": (first_quartile, third_quartile),
                                "density": density, "points": points}
    return grid, prepared

queue_minutes = {
    "north": [("N-41", 12), ("N-42", 13), ("N-43", 14), ("N-44", 14),
              ("N-45", 15), ("N-46", 16), ("N-47", 27)],
    "south": [("S-51", 11), ("S-52", 12), ("S-53", 12), ("S-54", 13),
              ("S-55", 18), ("S-56", 19), ("S-57", 20), ("S-58", 21)],
}
grid, clouds = prepare_latency_raincloud(queue_minutes, bandwidth_minutes=2)
assert len(grid) == 41 and clouds["north"]["median"] == 14
assert clouds["south"]["median"] == 15.5
assert len(clouds["north"]["points"]) == 7''',
        "cost": "Let N be the total observations across G groups and M the number of shared grid positions. Sorting within groups costs at most O(N log N); direct Gaussian density evaluation costs O(MN). Storage is O(N + GM) for raw points and density arrays. The two queue groups contain seven and eight recorded durations. North's median is 14 minutes; south's is 15.5. Both clouds use the same two-minute bandwidth and common value grid. Their density curves are normalized within group, so a taller peak does not mean more records. The stable identifier-derived offset affects only a point's cross-axis display position; the latency value and quartile calculation remain unchanged. For very large N, choose a tested KDE implementation or a binned approximation, and state the approximation in the export.",
        "mistakes": ["Letting each group or refresh pick its own bandwidth and then comparing the apparent number of modes.", "Interpreting equal-area density height as a sample count.", "Moving raw points along the measured value axis while calling it harmless jitter.", "Computing the cloud, quartiles and raw points from different filtered subsets.", "Hiding small group sizes behind a smooth cloud or omitting the quartile calculation policy."],
        "drill": "Compare two service queues with 47 and 83 eligible requests. Use one value domain and one predeclared bandwidth, keep every raw duration tied to a stable request ID, label both sample sizes, and check whether an apparent second peak remains after viewing the points and a binned histogram.",
        "related": [prefix + "box-violin-and-kde-bandwidth-for-group-comparisons", prefix + "beeswarm-plots-collision-spacing-and-sample-count", prefix + "uncertainty-and-small-sample-display", prefix + "small-multiples-shared-scales-and-facet-order"],
    },
]

publish(
    lessons,
    sort_start=8790,
    module_groups=[("Categorical transitions", [0]),
                   ("Time and frequency displays", [1]),
                   ("Composite distribution displays", [2])],
    incoming={
        "sankey-flow-conservation-and-unobserved-exits": [0],
        "cohort-retention-heatmaps-maturity-denominators-and-return-events": [0],
        "linked-filters-cohort-denominators-and-selection-state": [0],
        "chord-diagrams-directed-flows-self-loops-and-sector-totals": [0],
        "heatmap-missing-cells-and-color-domain": [1],
        "time-series-gaps-calendars-and-provisional-periods": [1],
        "large-series-level-of-detail-and-extrema": [1],
        "chart-export-manifest-data-and-render-version": [1],
        "box-violin-and-kde-bandwidth-for-group-comparisons": [2],
        "beeswarm-plots-collision-spacing-and-sample-count": [2],
        "uncertainty-and-small-sample-display": [2],
        "small-multiples-shared-scales-and-facet-order": [2],
    },
    packet_name="aitrove-data-visualization-import-20261010-c.json",
)
