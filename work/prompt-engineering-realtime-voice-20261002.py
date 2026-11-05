"""Add original real-time voice-agent prompt lessons, project, and quiz."""

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
production = "prompt-engineering/production"
projects = "prompt-engineering/projects"
quizzes = "prompt-engineering/quizzes"
project_path = "prompt-engineering/voice-library-renewal-project"
quiz_path = "quizzes/prompt-engineering-realtime-voice"

specs = [
    {
        "slug": "voice-turn-boundary-and-interim-text",
        "title": "Voice prompts: do not commit an action from interim speech",
        "summary": "Separate provisional recognition from a completed user turn and checked intent.",
        "definition": "A real-time voice agent receives audio in pieces. An interim transcript is a changing hypothesis, while a completed turn is a candidate for intent extraction. Prompt the model to treat interim words as context for listening, not as authority for an effectful tool call. The turn controller owns endpoint detection and can wait through a short pause; the prompt describes how to respond once the controller marks a turn ready. Preserve a timestamped record of the final recognized phrase and any low-confidence span. For short ambiguous commands, ask a targeted clarification instead of guessing from the first few syllables. A recognized transcript is still not proof of account identity or tool permission.",
        "case": "A library patron says, 'Renew BK-412—no, BK-421, if it is still available.' The recognizer briefly shows 'Renew BK-412' as an interim hypothesis. Calling the renewal tool at that moment would affect the wrong item. The final utterance corrects the identifier and adds a condition. The agent extracts BK-421, checks the patron's account scope and renewal eligibility, then states the item title before an effectful action. If café noise makes the final digit unclear, it asks which code the patron meant. It does not treat a moment of silence after 'BK-412' as proof that the user finished speaking.",
        "sample": "Interim at 00:02.1: Renew BK-412 -> listen only.\nFinal at 00:03.8: No, BK-421, if available.\nIntent: conditional renewal of BK-421; verify owner and eligibility.\nUnclear final digit -> ask for code; no renewal call.",
        "cost": "With U audio updates per turn, maintaining the latest interim text is O(U) event work and O(L) space for the retained transcript length L. A longer endpoint wait raises response latency but reduces premature cuts; a shorter wait does the opposite. Evaluate pauses, self-corrections, background speech, and code digits rather than tuning to one clean recording. Send the smallest useful final-turn record to the model instead of every partial hypothesis. The application should reject a tool call that lacks a finalized utterance and a verified account scope, regardless of the model's wording.",
        "mistakes": ["Do not turn an interim transcript into a renewal request.", "Do not assume a silence threshold always marks the end of a thought.", "Do not use recognized text as account authorization."],
        "related": ["prompt-engineering/audio-transcription-uncertainty", "prompt-engineering/audio-overlap-speaker-review", "prompt-engineering/clarification-versus-assumption-gate"],
        "section": applications,
    },
    {
        "slug": "voice-barge-in-and-playback-cancellation",
        "title": "Voice interruptions: stop stale speech before handling a new turn",
        "summary": "Cancel queued audio and reconcile what the caller actually heard.",
        "definition": "Barge-in occurs when a caller speaks while the agent is still talking. A prompt can tell the model to acknowledge a correction and avoid repeating a long answer, but the audio runtime must cancel or truncate unsent playback and identify the part already heard. Do not leave a generated sentence in conversation history as if the user heard it in full. The next turn should be based on the caller's new utterance and the last confirmed state. If an earlier tool call is in flight, interruption of speech does not cancel the server effect; handle the tool result separately. Distinguish noise from a genuine user interruption before discarding useful playback.",
        "case": "The library agent begins, 'BK-421 is due on the twenty—' when the patron cuts in: 'Wait, do not renew it; I only wanted the due date.' The runtime stops the remaining audio and records that the due-date sentence was incomplete. The agent treats the new turn as a correction. If no renewal call was made, it reports the date without changing the loan. If a renewal request was already sent, stopping the voice is not a rollback; it must check the receipt and tell the patron what happened. A cough near the microphone should not erase the answer without a confirmed speech start or a follow-up cue.",
        "sample": "Playback: 'BK-421 is due on the twenty—' [cancelled].\nCaller: 'Do not renew; due date only.'\nConversation state: spoken text truncated; new intent=read due date.\nIn-flight renewal? check receipt; audio cancellation is not undo.",
        "cost": "For N queued audio chunks, cancellation is O(N) queue cleanup in a simple implementation, while detecting barge-in adds continuous audio monitoring and can raise false interrupts in noisy rooms. Record the playback cursor or completed chunk count so dialogue state reflects what was delivered. Keep evaluation pairs for true interruption and incidental sound. Generating shorter spoken turns lowers the amount of stale audio that must be cancelled, yet overly fragmented speech can feel choppy. A prompt cannot guarantee timing; test the actual runtime with network jitter and a real microphone path.",
        "mistakes": ["Do not assume cancelled playback reverses an in-flight tool call.", "Do not summarize unheard audio as if it reached the caller.", "Do not treat every noise burst as a user correction."],
        "related": ["prompt-engineering/voice-turn-boundary-and-interim-text", "prompt-engineering/conversation-checkpoint-reconstruction", "prompt-engineering/side-effect-receipt-reconciliation"],
        "section": applications,
    },
    {
        "slug": "spoken-entity-confirmation-and-repair",
        "title": "Spoken confirmations: repeat the risky field, not the whole form",
        "summary": "Confirm names, codes, and dates when recognition error would change the action.",
        "definition": "A spoken confirmation should focus on fields whose misrecognition changes the requested result. Provide the model with the extracted value, a reason it may be uncertain, and a narrow question that lets the caller correct it. Reading back every known field wastes time and can disclose private details aloud in a shared space. For a book code, say the relevant digits and title only after the account check; ask the caller to confirm when two catalog records are plausible. After a correction, update the structured field and repeat just that field. The backend remains responsible for validating the identifier and eligibility. A polite 'yes' from a nearby speaker is not enough if speaker ownership is uncertain.",
        "case": "The caller says 'BK four two one' over a blender. Recognition candidates are BK-421 and BK-427. The agent has not yet opened a private account record, so it asks, 'Was that BK-421 or BK-427?' The patron replies, '421, the atlas.' Once authenticated, the catalog lookup finds 'Harbor Atlas' for BK-421. The agent confirms, 'Harbor Atlas, code BK-421—renew that item?' The patron says yes. It then checks the renewal rule. If the catalog instead maps BK-421 to another title, it stops rather than silently converting the request to the nearest match.",
        "sample": "Candidates: BK-421 / BK-427; noisy final digit.\nRepair question: 'Was that BK-421 or BK-427?'\nChecked title after account lookup: Harbor Atlas.\nEffect gate: confirmed BK-421 + eligible renewal + authenticated patron.",
        "cost": "If C recognition candidates require a catalog lookup, a naive flow may issue O(C) reads; a focused clarification can reduce reads when identifiers are distinct. Each extra confirmation turn adds speech latency, so reserve it for action-changing uncertainty and privacy-sensitive disclosure. Track wrong-entity actions and unnecessary confirmations separately. Use typed record IDs in the application and speak a human-checkable title only after access control. If the caller cannot confirm, offer a non-effectful way to continue rather than making a probabilistic renewal.",
        "mistakes": ["Do not use a low-confidence digit to select a record for an effectful call.", "Do not recite private account details before access is checked.", "Do not interpret a nearby voice as the account holder's confirmation."],
        "related": ["prompt-engineering/classification-rubric-and-unknown-label", "prompt-engineering/request-risk-routing-contract", "prompt-engineering/voice-turn-boundary-and-interim-text"],
        "section": applications,
    },
    {
        "slug": "voice-tool-wait-and-outcome-language",
        "title": "Voice tool waits: report progress without inventing an outcome",
        "summary": "Use short waiting utterances and distinguish pending, rejected, and confirmed effects.",
        "definition": "A voice agent should not fill tool latency with a fabricated success message. Prompt it to use a brief, truthful waiting phrase when a lookup or effectful call exceeds a chosen threshold, then speak only from the returned status or an authoritative follow-up read. Keep pending, confirmed, rejected, and ambiguous states separate. The runtime can emit a waiting cue without allowing the model to make another call. A timed-out renewal may have succeeded on the server; a retry requires receipt reconciliation. The spoken response must match the latest verified state, and a text receipt should carry exact details that are awkward to hear once over audio.",
        "case": "A renewal request for BK-421 takes 2.6 seconds. The agent says, 'I am checking the renewal,' not 'It is renewed.' The server returns receipt RN-638 with a new due date of 3 December. Only then does the agent say the renewal is confirmed and offer to send the details in text. In a second test the call times out after transmission. The agent says it cannot yet confirm the result, reads the account's current loan state, and does not submit a duplicate request. If the follow-up read is still stale, it hands the case to an operator with the request identifier rather than claiming rejection.",
        "sample": "At 1.2 s without result: 'I am checking the renewal.'\nReceipt RN-638; due 2026-12-03 -> confirmed wording.\nTimeout after send -> ambiguous; read loan state before retry.\nStale read -> operator review, not a second renewal.",
        "cost": "For T tool calls, each with a bounded timeout, the orchestration cost is O(T) state transitions plus network latency. A waiting phrase may make a delay easier to understand but adds speech output time, so trigger it only when the call is slow enough to justify it. Keep response templates keyed to verified statuses; this prevents a model from turning an empty response into a cheerful success. Store request identifiers and receipts in compact form for recovery. Measure both time to first truthful audio and time to confirmed completion, since optimizing only the first can reward premature claims.",
        "mistakes": ["Do not say an effect succeeded while its tool call is pending.", "Do not retry after a timeout without resolving the first attempt.", "Do not translate a stale account read into definitive failure."],
        "related": ["prompt-engineering/side-effect-receipt-reconciliation", "prompt-engineering/cost-latency-quality-budget", "prompt-engineering/browser-effect-receipt-and-recovery"],
        "section": applications,
    },
    {
        "slug": "realtime-voice-evaluation-slices",
        "title": "Real-time voice evaluations: test timing and state, not transcript fluency",
        "summary": "Cover noise, self-correction, barge-in, tool delay, and effect receipts as separate slices.",
        "definition": "A voice-agent evaluation needs synchronized input audio, recognition events, output audio, tool events, and a final account state. A text transcript alone hides early tool calls, unheard speech, and false interruption. Build cases for self-correction, pause inside a sentence, digit confusion, background speech, genuine barge-in, incidental noise, slow lookup, and ambiguous effect. Score whether the agent used a final turn, selected the right entity, confirmed action-changing fields, stopped stale playback, respected tool authority, and described the confirmed outcome. Set hard failures for wrong-account actions and duplicate effects. Review recordings with privacy controls because raw calls may contain sensitive speech.",
        "case": "A test suite for the library renewal agent contains 38 calls: 7 code corrections, 6 mid-sentence pauses, 5 noisy digit pairs, 5 true interruptions, 4 incidental sounds, 6 slow-tool cases, and 5 lost-response cases. A new prompt reduces repeated confirmations but renews BK-412 in one correction call before the final transcript says BK-421. That is a critical failure despite better average latency. The team records the audio event sequence, action time, receipt, and loan state, then blocks release. A separate case catches a false barge-in caused by a dropped metal cup; it counts as a usability defect, not a wrong-record effect.",
        "sample": "Case VC-17: interim BK-412; final BK-421; no call before final.\nCase VC-24: cup noise; playback should continue.\nCase VC-31: submit timeout; one receipt or ambiguous state.\nRelease: zero wrong-record renewals and zero duplicate effects.",
        "cost": "For C recorded calls, V prompt variants, and M review modes, exhaustive comparison takes O(CVM) runs plus audio playback time proportional to total duration. Automated event assertions can catch early calls and duplicate receipts, while human listening is needed for intelligibility and false interrupts. Keep a fixed critical set on every candidate release and sample less risky pronunciation variants separately. Store model, recognizer, endpoint, voice, and tool versions with each case; a prompt comparison is misleading when the audio pipeline changed at the same time. Minimize recording retention and access to raw speech.",
        "mistakes": ["Do not grade voice behavior from the final transcript alone.", "Do not average a wrong-record renewal away with lower latency.", "Do not compare prompt variants across different audio-pipeline versions without recording the difference."],
        "related": ["prompt-engineering/evaluation-slice-design", "prompt-engineering/paired-prompt-evaluation-uncertainty", "prompt-engineering/audio-overlap-speaker-review"],
        "section": production,
    },
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]).intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: a voice call that renews the right library item"
titles[quiz_path] = "Real-time voice prompt decisions"


def link(path):
    assert path in titles, path
    return f'<a href="/{html.escape(path)}">{html.escape(titles[path])}</a>'


def links(selected):
    return "<ul>" + "".join(f"<li>{link(path)}</li>" for path in dict.fromkeys(selected)) + "</ul>"


def related(selected):
    return [{"path": path, "title": titles[path]} for path in dict.fromkeys(selected)]


def article(path, title, summary, body, section, order, connections, kind="tutorial"):
    entry = copy.deepcopy(lookup["prompt-engineering/evaluation-slice-design"])
    subject = "prompt-engineering-applications" if section == applications else "prompt-engineering-production" if section == production else "prompt-engineering-project"
    entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + path)),
                 path=path, title=title, summary=summary, body=body,
                 subject=subject, difficulty="Advanced", tags=["prompt engineering", "voice agents"],
                 sort_order=29000 + order, status="published", published_at=stamp,
                 created_at=stamp, updated_at=stamp)
    entry["data"].update(kind=kind, reading_minutes=11 if kind == "tutorial" else 19,
                         author_path="authors/aitrove-editorial", subject_root=subject_root,
                         section_path=section, content_format="html", seo_ready=True,
                         related=related(connections))
    return entry


new_rows = []
for index, (path, spec) in enumerate(zip(paths, specs)):
    connections = [spec["section"], subject_root] + spec["related"] + [peer for peer in paths if peer != path] + [project_path, quiz_path]
    body = ("<p>" + html.escape(spec["definition"]) + "</p>"
            + "<h2>Operational case</h2><p>" + html.escape(spec["case"]) + "</p>"
            + '<pre><code class="language-text">' + html.escape(spec["sample"], quote=False) + "</code></pre>"
            + "<h2>Performance and operating cost</h2><p>" + html.escape(spec["cost"]) + "</p>"
            + "<h3>Common Mistakes</h3><ul>" + "".join("<li>" + html.escape(mistake) + "</li>" for mistake in spec["mistakes"]) + "</ul>"
            + "<h2>Connected lessons</h2>" + links(connections))
    new_rows.append(article(path, spec["title"], spec["summary"], body, spec["section"], index * 10, connections))

project_connections = paths + ["prompt-engineering/audio-transcription-uncertainty", "prompt-engineering/side-effect-receipt-reconciliation", "prompt-engineering/voice-barge-in-and-playback-cancellation", quiz_path]
project_body = (
    "<p>Design a fictional library voice assistant for one authorized task: renew the patron's loan of BK-421 if eligible. The caller is in a café, the recognition stream is provisional, and a separate catalog and loan service own the actual state. Produce a prompt contract, an event trace, and a release decision. The prompt can request clarification and state tool results; it cannot make interim speech final, cancel audio by itself, or authorize a loan from a recognized sentence alone. The application checks identity, renewal rules, and receipts.</p>"
    "<h2>Build the call path</h2><p>Begin with the utterance 'Renew BK-412—no, BK-421, if it is still available.' Show the interim and final transcript separately and assert that no renewal call occurs before the final turn. Inject blender noise so the last digit could also be seven. The agent asks a focused code question, then checks the catalog title after account access is verified. Once the patron confirms Harbor Atlas, code BK-421, it asks for explicit renewal confirmation. A nearby 'yes' from another voice is not sufficient unless the caller can be identified. Keep the due-date lookup read-only until the requested effect is clear.</p>"
    "<h2>Interrupt and recover</h2><p>While the assistant begins a due-date sentence, the patron says, 'Wait, do not renew; due date only.' Stop queued speech, preserve the portion actually spoken, and process the new intent. If a renewal call was already transmitted, do not claim the interruption undid it; reconcile the receipt. Add a 2.6-second tool delay with a truthful waiting phrase. In one case the server returns receipt RN-638 and a new due date of 3 December. In another, the response is lost and the loan view is stale: the spoken status remains uncertain, no blind retry occurs, and a review path receives the request identifier.</p>"
    '<pre><code class="language-text">Interim: BK-412 -> no tool effect. Final: correction to BK-421.\nNoisy digit: BK-421 or BK-427 -> ask narrowly.\nBarge-in: stop unheard audio; check any transmitted effect.\nSlow tool: say checking, not renewed.\nReceipt RN-638 -> confirmed; lost response -> reconcile.</code></pre>'
    "<h2>Performance and operating cost</h2><p>Let C be test calls, V prompt variants, and M review modes. A broad comparison uses O(CVM) runs, plus listening time proportional to recorded duration. Each extra confirmation turn adds latency; each early action risks the wrong loan. Measure the time to the first truthful spoken response and the time to a confirmed result separately. Preserve recognizer, endpoint, model, voice, and tool versions so a prompt change is not confused with a pipeline change. The release gate blocks any wrong-record renewal or duplicate effect, even when average latency improves.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not call the renewal tool from an interim transcript.</li><li>Do not assume stopping speech reverses a server request.</li><li>Do not report a renewal as complete without a receipt or authoritative state.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Test turn detection, noisy identifiers, interruption, tool latency, and receipt recovery in one voice call.", project_body, projects, 60, project_connections, kind="project"))

questions = [
    ("An interim transcript says BK-412, then the caller corrects it to BK-421. When may an effectful call be considered?", "After a final turn, identity check, and action confirmation", "As soon as BK-412 appears", "When the audio first becomes quiet", "Interim hypotheses can change before the turn is complete."),
    ("A short pause follows the item code. What should endpoint control consider?", "The caller may still be continuing or correcting the request", "The request must be final", "The account is authenticated", "Silence alone can cut a thought short."),
    ("The caller interrupts while audio is queued. Which component must stop the stale sound?", "The audio runtime", "The prompt text alone", "The catalog database", "Playback cancellation is an execution action."),
    ("Does cancelling spoken output undo a renewal request already sent?", "No; check the tool result or receipt", "Yes, automatically", "Only if the caller repeats the code", "Audio and server effects have separate state."),
    ("BK-421 and BK-427 are plausible after a noisy digit. What fits?", "Ask a narrow code clarification", "Choose the most likely code", "Renew both", "Action-changing uncertainty needs repair."),
    ("When is it appropriate to speak a private catalog title from an account?", "After access to the account is checked", "Before authentication for speed", "Whenever background speech says yes", "Recognition does not grant account scope."),
    ("A renewal tool is slow. What is truthful to say?", "I am checking the renewal", "The book is renewed", "The request was rejected", "Pending is not confirmed or rejected."),
    ("A tool response is lost after transmission. Which status fits?", "Ambiguous until receipt or account state is checked", "Definite failure", "Definite success", "A missing response does not reveal server state."),
    ("A stale read still shows the old due date. What must be avoided?", "A blind second renewal call", "A bounded receipt lookup", "An uncertain status report", "Eventually consistent state may lag the effect."),
    ("Why is a final transcript insufficient to grade barge-in?", "It omits playback timing and what the caller heard", "It always includes tool receipts", "It proves speaker identity", "The event sequence determines interruption behavior."),
    ("A new prompt reduces latency but renews the wrong code once. Release?", "Block on the wrong-record effect", "Publish based on average speed", "Ignore the correction case", "Critical errors cannot be averaged away."),
    ("Which versions make a voice regression reproducible?", "Recognizer, endpoint, model, voice, prompt, and tools", "Prompt text alone", "Only the catalog item title", "Pipeline changes can alter turn and playback behavior."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-multimodal-evidence"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Test interim speech, interruption, confirmation, tool waits, and voice evaluation.",
                  body="<p>Choose the boundary that preserves a correct voice action and an honest spoken status.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
                  sort_order=29070, status="published", published_at=stamp,
                  created_at=stamp, updated_at=stamp)
quiz_entry["data"].update(subject_root=subject_root, section_path=quizzes,
                          content_format="html", author_path="authors/aitrove-editorial",
                          seo_ready=True, duration_minutes=12,
                          related=related(paths + [project_path]),
                          questions=[{"prompt": prompt,
                                      "options": ([correct, wrong_a, wrong_b][index % 3:] + [correct, wrong_a, wrong_b][:index % 3]),
                                      "answer": (-index) % 3, "explanation": explanation}
                                     for index, (prompt, correct, wrong_a, wrong_b, explanation) in enumerate(questions)])
new_rows.append(quiz_entry)

for hub_path, selected, title, summary in [
    (applications, paths[:4], "Real-time voice contracts", "Keep interim speech, interruption, entity repair, and tool waits in separate states."),
    (production, paths[4:], "Voice-agent evaluation", "Test event timing, noise, receipts, and final account state."),
    (projects, [project_path], "Library renewal voice call", "Verify one effectful task under corrections, noise, interruption, and delay."),
    (quizzes, [quiz_path], "Real-time voice decisions", "Check turn, playback, entity, and outcome boundaries."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>Real-time voice prompt contracts</h2><p>Separate speech hypotheses, playback, tool effects, and verified spoken outcomes.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/audio-transcription-uncertainty": paths[0],
    "prompt-engineering/audio-overlap-speaker-review": paths[2],
    "prompt-engineering/clarification-versus-assumption-gate": paths[2],
    "prompt-engineering/conversation-checkpoint-reconstruction": paths[1],
    "prompt-engineering/cost-latency-quality-budget": paths[3],
    "prompt-engineering/side-effect-receipt-reconciliation": paths[3],
    "prompt-engineering/evaluation-slice-design": paths[4],
}
for old_path, new_path in backlinks.items():
    entry = lookup[old_path]
    entry["body"] += "<p><strong>Continue with:</strong> " + link(new_path) + ".</p>"
    entry["data"]["related"] = related([item["path"] for item in entry["data"].get("related", [])] + [new_path])
    entry["updated_at"] = stamp

entries.extend(new_rows)
fixture.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"newLessons": len(specs), "newProjects": 1, "newQuizzes": 1,
                  "newPaths": [entry["path"] for entry in new_rows]}))
