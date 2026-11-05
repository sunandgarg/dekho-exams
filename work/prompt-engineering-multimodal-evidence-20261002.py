"""Add multimodal evidence contracts, a worked project, and a decision quiz."""

import copy
import datetime
import html
import json
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
fixture = root / "src/data/fixtures.json"
entries = json.loads(fixture.read_text())
lookup = {entry["path"]: entry for entry in entries}
stamp = datetime.datetime.now(datetime.UTC).isoformat()
subject_root = "prompt-engineering/prompt-engineering"
applications = "prompt-engineering/applications"
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"
project_path = "prompt-engineering/warehouse-evidence-reconciliation-project"
quiz_path = "quizzes/prompt-engineering-multimodal-evidence"

specs = [
    {
        "slug": "document-page-anchor-and-field-conflict",
        "title": "Document prompts: anchor each field to a page and resolve conflicts",
        "summary": "Extract a field with its page location, source state, and conflict status.",
        "definition": "A document extraction prompt should return a field only with the page and region that support it, along with an explicit unknown or conflict state. OCR text may separate a value from its label or move a table cell into the wrong row. A prompt can help interpret the layout, but it cannot make a low-quality scan legible or settle a disagreement between signed pages by assertion. Preserve the raw document ID, page numbering convention, extraction version, and field-level evidence. Validate types and reconcile business rules outside the model before writing a system of record.",
        "case": "A warehouse packet contains delivery note DN-684. Page 2 lists 47 crates in the dispatch table; page 5 has a handwritten correction to 44, signed by a receiver but not by the driver. A text-only extraction joins the 44 with the wrong row. The assistant must return both observed quantities, their page anchors, and a conflict state. The receiving system blocks automatic inventory adjustment until an operator verifies whether the correction applies to this shipment. A clearer prompt may improve field placement, but it cannot manufacture the missing driver acknowledgement.",
        "sample": "Document: DN-684; pages use visible printed numbers.\nquantity_observations: 47 at page 2/table row 6; 44 at page 5/note box.\nconflict: true; accepted_quantity: unknown.\nReview reason: handwritten correction lacks driver acknowledgement.\nWrite gate: no inventory update until authorized reconciliation.",
        "cost": "Reading P pages with C candidate fields produces at least O(P + C) extraction and validation work, while image processing and model calls dominate wall time. Keeping page crops for disputed fields increases storage and review time. Ask only for the fields needed by the workflow, and route ambiguous handwriting to a reviewer. A high field confidence score does not resolve a disagreement between two visible values. The expensive error is a silent wrong-row match that propagates into inventory, so measure field-to-region accuracy as well as text accuracy.",
        "mistakes": ["Do not return a value without its page or region evidence.", "Do not treat OCR confidence as proof that conflicting pages agree.", "Do not update inventory from an unresolved extracted quantity."],
        "related": ["prompt-engineering/structured-document-extraction", "prompt-engineering/evidence-id-traceability", "prompt-engineering/human-review-escalation"],
    },
    {
        "slug": "image-region-verification-contract",
        "title": "Image prompts: verify claims against named regions and crops",
        "summary": "Separate visible observations from object identity and unsupported inference.",
        "definition": "An image verification prompt asks for an observation tied to a particular image region, then records what the image cannot establish. A model may describe a dent or read a label, but the crop, resolution, angle, and lighting determine what is actually visible. Use stable image IDs and region coordinates or crop IDs, and inspect the source image when a claim affects a decision. Do not infer serial numbers, material defects, or causation from a vague global caption. A region annotation is evidence location, not a guarantee that the interpretation is correct.",
        "case": "Photo PH-309 shows three stacked cartons beside a pallet. A broad caption says the top carton is damaged. The visible tear is actually on the lower right carton, while the top carton has a shadow along its seam. The team asks the assistant to identify the affected carton by position, crop ID, and visible feature. A reviewer zooms into crop CR-8 and confirms a torn edge but cannot read the pallet label. The output records the tear and the unreadable label separately. It does not declare that the shipment was damaged in transit; the photo alone lacks timing and chain of custody.",
        "sample": "Image PH-309; region CR-8: lower-right carton, torn outer edge.\nImage PH-309; region CR-9: pallet label unreadable.\nObservation: visible tear; object identity: provisional.\nUnsupported: damage time, responsible party, hidden contents.\nDecision: request a label close-up before matching shipment ID.",
        "cost": "A full-image pass plus K targeted crops takes O(K) additional model or review steps and can increase image-token and storage costs. Crop only where the acceptance check needs detail; a crop that removes neighboring objects may destroy positional context, so retain its source coordinates. Review workload rises with ambiguous images, but false certainty is costlier when a photo drives a claim. Measure localization errors and missed unreadable labels separately. If the image is too small, request a better capture instead of enlarging an invented detail.",
        "mistakes": ["Do not claim a precise object identity from a wide image with unreadable labels.", "Do not let a tight crop erase the context needed to locate an object.", "Do not infer cause or timing from a single still image."],
        "related": ["prompt-engineering/image-generation-brief-and-review", "prompt-engineering/multimodal-evidence-boundary", "prompt-engineering/selective-prediction-thresholds"],
    },
    {
        "slug": "audio-overlap-speaker-review",
        "title": "Audio prompts: mark overlapping speech before assigning speakers",
        "summary": "Keep diarization, transcription, and attribution as separate claims.",
        "definition": "An audio prompt can request words, time ranges, speaker labels, and uncertainty, but these are different outputs with different failure modes. During overlapping speech, a transcript may contain words without a defensible speaker assignment. Use neutral speaker IDs until identity is independently established. Mark overlap spans and unintelligible segments rather than forcing one clean dialogue. If a statement would change an operational decision, replay the original audio near that time and compare it with the transcript. A speaker label is a hypothesis, not proof of who was present.",
        "case": "A driver calls the warehouse at 14:27. Two people talk at once while one says 'forty-four' and another says 'forty-seven'. The initial transcript assigns both phrases to the driver and turns the call into a false agreement about delivery quantity. The revised contract emits an overlap interval, two uncertain phrases, and speaker IDs S1 and S2 without names. A reviewer listens to the source segment and confirms that the driver said 47; the other voice remains unidentified. The inventory discrepancy still requires the signed document check. The audio result cannot replace it.",
        "sample": "Audio AU-152; interval 02:13-02:19; overlap: true.\nS1: 'forty-seven' [reviewed]; identity: driver [verified separately].\nS2: 'forty-four' [uncertain]; identity: unknown.\nNo consensus statement; quantity remains disputed.\nReview: replay source audio from 02:11 through 02:21.",
        "cost": "For a recording of duration T, one transcription pass is roughly proportional to T in media processed; replaying J disputed spans adds the sum of their durations. Word-level timestamps and diarization increase output size and review time. Send only the relevant interval for a second check, but retain enough lead-in to identify turns. The operational cost is not just model latency: human listening and identity verification may dominate. Track word errors, missed overlaps, and wrong-speaker attributions separately, because a readable transcript can still assign a statement to the wrong person.",
        "mistakes": ["Do not force one speaker label across overlapping voices.", "Do not turn an uncertain phrase into an agreement between parties.", "Do not equate a model-assigned speaker ID with a verified identity."],
        "related": ["prompt-engineering/audio-transcription-uncertainty", "prompt-engineering/clarification-versus-assumption-gate", "prompt-engineering/evidence-id-traceability"],
    },
    {
        "slug": "video-frame-sampling-disclosure",
        "title": "Video prompts: disclose sampling gaps around short events",
        "summary": "Distinguish events seen in frames from events inferred between them.",
        "definition": "A video summary should identify its inspected time ranges and sampling method when a brief event matters. A frame sampled every few seconds can miss a one-second handoff, and a transcript cannot prove a visual event. Ask the model for observations with time bounds and modality, then re-inspect intervals near a consequential claim at finer resolution or by direct playback. Do not turn 'not seen in sampled frames' into 'did not happen'. Keep the original video ID, clip offsets, and frame timestamps in the evidence record so another reviewer can reproduce the observation.",
        "case": "Camera clip VD-441 covers a loading bay from 09:14 to 09:19. A coarse scan shows the pallet before and after a driver approaches but misses a brief label swap at 09:16:42. A summary claiming 'no label change' is unsupported because the sampled frames did not cover that second. The reviewer inspects 09:16:35-09:16:50 more closely and records a hand reaching the pallet, but the label characters remain unreadable. The correct result is a visible interaction with uncertain label identity. A separate close-up or inventory log is needed before the team assigns the pallet to a shipment.",
        "sample": "Video VD-441; coarse frames: one every 4 seconds.\nClaim under review: label changed at 09:16:42.\nCoarse result: event not observed; absence not established.\nFocused review: 09:16:35-09:16:50; hand reaches pallet.\nLabel text: unreadable; shipment identity: unresolved.",
        "cost": "For duration T and sample rate F, static frame inspection grows roughly O(TF) in frames, tokens, and transfer work. Higher F improves coverage of short events but costs more and still cannot recover detail absent from the recording. A two-stage pass can inspect the full clip coarsely and then targeted intervals densely; record that search path to avoid presenting a focused result as exhaustive coverage. Manual playback adds time but may be necessary when an event is close to the decision threshold. Measure missed-event rate on clips with known brief events.",
        "mistakes": ["Do not claim an event never happened from sparse sampled frames.", "Do not cite an audio statement as visual proof of a label change.", "Do not invent readable text where the source frame is blurred."],
        "related": ["prompt-engineering/video-timecode-evidence", "prompt-engineering/multimodal-evidence-boundary", "prompt-engineering/evaluation-slice-design"],
    },
    {
        "slug": "cross-modal-conflict-ledger",
        "title": "Cross-modal evidence: keep conflicting observations separate",
        "summary": "Reconcile document, image, audio, and video claims without flattening uncertainty.",
        "definition": "A cross-modal evidence ledger stores each claim with its source, location, observation type, and verification state. It prevents a summary from merging a document value, an audio utterance, and a photo interpretation into one falsely certain fact. Specify which source is authoritative for each field and which conflicts require human review. Matching IDs across media can be useful, but an apparent match is not proof when labels are unreadable or timestamps are inconsistent. The prompt should report unresolved conflicts and the next discriminating check; a server rule decides whether any downstream effect is allowed.",
        "case": "A delivery note says 47 crates, a signed correction says 44, a call contains both numbers during overlap, and a camera clip shows one pallet interaction without a readable label. A generic summary might say the driver confirmed 44 damaged crates. The ledger instead records four separate observations and no confirmed quantity or damage cause. The operator checks the receiving scan for crate IDs and seeks a better label image. Until then, the assistant can prepare a review packet but cannot post an inventory adjustment. The conflict is the useful result, not a defect to smooth away.",
        "sample": "DN-684/p2: 47 crates; printed dispatch table.\nDN-684/p5: 44 crates; handwritten signed correction.\nAU-152/02:13-02:19: two numbers in overlapping speech.\nVD-441/09:16:35-09:16:50: pallet interaction; label unreadable.\nResolved quantity: unknown; next check: receiving scan by crate ID.\nEffect gate: hold inventory adjustment.",
        "cost": "For S source observations, building a ledger is O(S), while naive all-pairs conflict checking is O(S squared); indexing by field and shipment ID keeps routine comparison closer to the number of relevant observations. Review cost grows with consequential conflicts, so avoid sending unrelated media into the prompt. A compact ledger is cheaper to audit than a long narrative that loses provenance. Retain source pointers and verification states, not unnecessary copies of private media. Wrongly collapsing two observations may save a review minute and create a much larger correction later.",
        "mistakes": ["Do not treat repeated claims across media as independent proof when they share an origin.", "Do not pick the most fluent observation as the authoritative record.", "Do not perform an external adjustment while the decisive field is unresolved."],
        "related": ["prompt-engineering/evidence-id-traceability", "prompt-engineering/human-review-escalation", "prompt-engineering/side-effect-receipt-reconciliation"],
    },
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
new_paths = set(paths + [project_path, quiz_path])
assert not new_paths.intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: reconcile a warehouse evidence packet"
titles[quiz_path] = "Multimodal prompt evidence decisions"


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(paths_to_link):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(paths_to_link)) + "</ul>"


def related(paths_to_link):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(paths_to_link)]


def article(path, title, summary, body, section, order, connections, kind="tutorial"):
    entry = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)),
                 path=path, title=title, summary=summary, body=body,
                 subject="prompt-engineering-applications" if section == applications else "prompt-engineering-project",
                 difficulty="Advanced", tags=["prompt engineering", "multimodal evidence"],
                 sort_order=order, status="published", published_at=stamp,
                 created_at=stamp, updated_at=stamp)
    entry["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 18,
                         author_path="authors/aitrove-editorial", subject_root=subject_root,
                         section_path=section, content_format="html", seo_ready=True,
                         related=related(connections))
    return entry


new_rows = []
for index, (path, spec) in enumerate(zip(paths, specs)):
    peers = [other for other in paths if other != path]
    connections = [applications, subject_root] + spec["related"] + peers + [project_path, quiz_path]
    body = (
        "<p>" + html.escape(spec["definition"]) + "</p>"
        "<h2>Decision in practice</h2><p>" + html.escape(spec["case"]) + "</p>"
        '<pre><code class="language-text">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
        "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
        "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(item) + "</li>" for item in spec["mistakes"]) + "</ul>"
        "<h2>Connected lessons</h2>" + links(connections)
    )
    new_rows.append(article(path, spec["title"], spec["summary"], body,
                            applications, 26400 + index * 10, connections))

project_connections = paths + ["prompt-engineering/structured-document-extraction",
                                "prompt-engineering/multimodal-evidence-boundary", quiz_path]
project_body = (
    "<p>This project asks an assistant to prepare a warehouse discrepancy packet without deciding inventory quantity on incomplete media. The fictional shipment has a delivery note, a photo of the pallet, a short driver call, and a loading-bay video. Each modality can contribute an observation, but none can grant approval to change the stock ledger. The deliverable is an evidence ledger, conflict statement, next-check plan, and explicit no-effect decision.</p>"
    "<h2>Inspect each source in its own terms</h2><p>Read DN-684 as a multipage document. Preserve 47 crates from the printed dispatch row on page 2 and 44 from the handwritten correction on page 5; record both anchors. In photo PH-309, identify a tear on the lower-right carton using crop CR-8, but mark the pallet label unreadable. In call AU-152, mark the two quantity phrases as overlapping speech and keep speaker identity separate from the transcript. For video VD-441, record the coarse sampling interval before focusing on 09:16:35-09:16:50. A hand reaches the pallet, but the frames cannot establish the label text.</p>"
    "<h2>Reconcile without inventing agreement</h2><p>Join observations by the shipment ID only where that ID is visible or separately verified. The phone call does not prove the signed correction; the camera clip does not prove which pallet was handled. The resulting ledger should say quantity unknown, tear visible on one carton, shipment match provisional, and cause of damage unknown. Ask the receiving clerk for the crate-ID scan and a readable label image. The server must hold the inventory adjustment until an authorized operator resolves the discrepancy. A later correction should add a new ledger revision rather than erasing the original observations.</p>"
    '<pre><code class="language-text">Packet: DN-684, PH-309, AU-152, VD-441.\nPrinted quantity: 47; corrected quantity: 44; status: conflict.\nPhoto: lower-right carton tear; pallet label unreadable.\nAudio: overlapping quantity phrases; no verified consensus.\nVideo: pallet interaction; label identity unresolved.\nNext checks: crate-ID receiving scan and label close-up.\nEffect: hold inventory adjustment; preserve evidence ledger.</code></pre>'
    "<h2>Performance and operating cost</h2><p>One pass over each medium costs four processing steps before any targeted recheck. Additional page crops, audio replay, and denser video inspection grow with the number of disputed regions rather than the whole packet when the team preserves source offsets. Comparing S observations by shipment and field is near O(S) with an index. Human verification still takes time, but it prevents the assistant from turning an unresolved quantity into a stock change. Keep media references and redacted review artifacts according to the workflow's retention rules.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not average 47 and 44 into a fictional quantity.</li><li>Do not call an overlapping phrase a verified driver agreement.</li><li>Do not treat a video sampling gap as proof of no label change.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections)
)
new_rows.append(article(project_path, titles[project_path],
                        "Reconcile a delivery note, photo, call, and video without inventing a shipment decision.",
                        project_body, projects, 26460, project_connections, kind="project"))

questions = [
    ("A document has 47 crates on page 2 and a signed correction to 44 on page 5. What should extraction return?", "Both anchored observations and a conflict state", "Only the newest number", "The average quantity", "The field is unresolved until the correction is reconciled."),
    ("Why keep a page or region anchor with a field?", "It lets a reviewer verify the visible source", "It proves the field is correct", "It grants write permission", "Location supports inspection but does not guarantee interpretation."),
    ("A wide photo shows a torn carton but the pallet label is unreadable. Which claim is supported?", "A visible tear at a named region", "The exact shipment ID", "The time the damage occurred", "The image supports the tear, not the missing label or cause."),
    ("What should be retained when a crop is used for verification?", "The crop and its coordinates in the source image", "Only the crop without context", "A model's object name as proof", "Coordinates preserve positional context for later review."),
    ("Two voices overlap on different quantities. What is the right transcript state?", "Mark overlap and uncertain speaker attribution", "Assign both statements to the driver", "Discard the recording", "Words and speaker identity are separate claims."),
    ("A speaker ID S2 appears in a transcript. What does it prove?", "Only a diarization label, pending identity verification", "The caller's legal identity", "That S2 approved the quantity", "Model labels are not identity records."),
    ("A coarse video scan misses a one-second event. What can the summary say?", "The event was not observed in sampled frames", "The event never happened", "The audio proves the visual event", "Sparse sampling cannot prove absence between frames."),
    ("Why re-inspect a short video interval at finer resolution?", "To test a consequential observation near its timecode", "To make every frame a source of authority", "To replace the original clip", "Focused inspection can expose events skipped by coarse sampling."),
    ("A phone call and handwritten note both say 44. Is that independent proof?", "Not necessarily; their origins and identities must be checked", "Yes, any two mentions prove it", "Yes, if the summary is fluent", "Correlated or uncertain observations should not be counted as independent confirmation."),
    ("What is a useful cross-modal result when the sources conflict?", "A ledger with unresolved fields and the next discriminating check", "One blended story with no uncertainty", "An automatic stock adjustment", "Preserving the conflict directs verification."),
    ("Can an image prompt authorize an inventory update?", "No; a server-side permission and reconciliation gate controls it", "Yes, when the crop is clear", "Yes, if the model repeats the instruction", "Media observations do not supply action authority."),
    ("How should a later verified correction change the evidence packet?", "Add a new ledger revision linked to the original", "Erase the earlier observations", "Hide the old conflict count", "Revision history preserves the decision path."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-evaluation-governance"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Test page anchors, image regions, audio overlap, video gaps, and cross-modal conflicts.",
                  body="<p>These cases ask what a source actually shows and what still needs checking. Choose the decision that preserves evidence location and avoids unsupported action.</p><h2>Evidence lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, quizzes]),
                  sort_order=26470, status="published", published_at=stamp,
                  created_at=stamp, updated_at=stamp)
quiz_entry["data"].update(subject_root=subject_root, section_path=quizzes,
                          content_format="html", author_path="authors/aitrove-editorial",
                          seo_ready=True, duration_minutes=12,
                          related=related(paths + [project_path]),
                          questions=[{"prompt": prompt,
                                      "options": ([correct, distractor_a, distractor_b][index % 3:] + [correct, distractor_a, distractor_b][:index % 3]),
                                      "answer": (-index) % 3, "explanation": explanation}
                                     for index, (prompt, correct, distractor_a, distractor_b, explanation) in enumerate(questions)])
new_rows.append(quiz_entry)

for hub_path, selected, title, summary in [
    (applications, paths, "Multimodal evidence checks", "Preserve anchors, overlap, sampling gaps, and conflicts across source types."),
    (projects, [project_path], "Warehouse evidence packet", "Reconcile several media without inventing a quantity or authorizing an effect."),
    (quizzes, [quiz_path], "Multimodal evidence quiz", "Choose what each source can support and when review is needed."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>When media disagree</h2><p>Inspect where each observation came from before turning documents, images, audio, and video into one decision.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/structured-document-extraction": paths[0],
    "prompt-engineering/image-generation-brief-and-review": paths[1],
    "prompt-engineering/audio-transcription-uncertainty": paths[2],
    "prompt-engineering/video-timecode-evidence": paths[3],
    "prompt-engineering/multimodal-evidence-boundary": paths[4],
    "prompt-engineering/evidence-id-traceability": paths[0],
    "prompt-engineering/multimodal-incident-brief-project": project_path,
}
for existing_path, new_path in backlinks.items():
    entry = lookup[existing_path]
    entry["body"] += "<p><strong>Continue with:</strong> " + link(new_path) + ".</p>"
    entry["data"]["related"] = related([item["path"] for item in entry["data"]["related"]] + [new_path])
    entry["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newLessons": len(specs), "newProjects": 1, "newQuizzes": 1,
                  "newPaths": [entry["path"] for entry in new_rows]}))
