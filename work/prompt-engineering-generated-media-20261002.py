"""Add original speech and video generation prompt contracts, project, and quiz."""

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
project_path = "prompt-engineering/museum-audio-video-brief-project"
quiz_path = "quizzes/prompt-engineering-generated-media"

specs = [
    {
        "slug": "speech-generation-script-and-direction",
        "title": "Speech generation prompts: lock words before directing delivery",
        "summary": "Keep approved narration separate from voice style, pacing, and rendering settings.",
        "definition": "A speech-generation contract has two different inputs: the exact approved words and the delivery direction. The prompt may specify a calm pace, short pauses at sentence boundaries, and the intended audience, but it should not invite the model to rewrite facts while speaking. Store script and voice settings as versioned fields. If the generator can change wording, compare a transcript of the rendered audio with the approved script and route deviations for review. Treat duration as a measured output; a requested 34-second read is not proof that the audio lasts 34 seconds. Provide a text alternative for listeners who cannot use the audio, and retain the actual audio file version used for review.",
        "case": "A fictional museum prepares a short guide for the Orin Dial, a 47-centimeter display model with 13 brass markers. The approved script says the markers are decorative and the dial does not measure time. A draft audio prompt asks for 'a lively explanation of the clock,' causing the model to describe the object as a working clock. The production prompt instead supplies the exact script, names the adult gallery audience, and requests a measured pace with a pause after the first sentence. The editor checks the rendered words and duration. If the generator omits 'does not measure time,' the clip fails even if its voice sounds natural.",
        "sample": "SCRIPT v3: 'The Orin Dial is a 47-centimeter display model.\nIts 13 brass markers are decorative. It does not measure time.'\nDIRECTION: measured pace; brief pause after sentence one.\nCHECK: transcribe rendered audio; compare factual phrases and duration.",
        "cost": "For N script tokens, a text comparison is O(N) after transcription, but listening to an audio clip of duration D takes O(D) human time at normal playback speed. A transcript match cannot catch clipped syllables, harsh volume changes, or a pause that obscures meaning. A shorter script may reduce generation time and review burden; compressing away a factual qualifier does the opposite of the intended work. Keep separate fields for script version, voice configuration, model, and rendered asset hash so a changed voice does not silently carry an old unreviewed narration.",
        "mistakes": ["Do not let a style request rewrite approved factual wording.", "Do not assume a target duration equals the rendered duration.", "Do not accept a matching transcript as proof that the audio is intelligible."],
        "related": ["prompt-engineering/audio-transcription-uncertainty", "prompt-engineering/caption-transcript-evidence-contract", "prompt-engineering/output-budget-and-completeness-contract"],
        "section": applications,
    },
    {
        "slug": "speech-pronunciation-and-number-contract",
        "title": "Speech pronunciation prompts: resolve names and numbers explicitly",
        "summary": "Use an approved reading guide for unusual terms, measurements, and ambiguous numerals.",
        "definition": "A written token does not always have one obvious spoken form. A speech prompt should keep the displayed text and its approved reading separate. Provide pronunciations for names, expansions for abbreviations, and rules for dates, units, and identifiers. If the synthesis engine supports a lexicon or speech markup, validate the syntax and language setting for that engine; otherwise use an approved spoken script. Do not assume a model will say '47 cm' or 'XQ-74' in the way the editor expects. Check the rendered audio, not only the prompt text. A pronunciation guide cannot repair a wrong underlying fact, so compare numbers with the approved record before rendering.",
        "case": "The museum calls its invented exhibit 'Orin' and approves the spoken reading 'OR-in.' A generator instead says 'oh-REEN' in one clip. In the same script, it reads the inventory code XQ-74 as a quantity and says 'seventy-four' without the letters. The public narration does not need that internal code, so the editor removes it rather than overloading the audience with a technical identifier. The 47-centimeter height and 13 brass markers do matter; their spoken forms are written in the recording brief. A reviewer listens for both values and the approved name, then checks that the visible exhibit label uses the same name.",
        "sample": "Display: Orin Dial | 47 cm | 13 brass markers.\nApproved speech: 'OR-in Dial; forty-seven centimeters; thirteen brass markers.'\nInternal code XQ-74: omit from public narration.\nReview: name, measurements, and label agree in rendered media.",
        "cost": "For K special terms and N narration segments, a pronunciation checklist requires O(KN) naive listening checks; indexing each term's timecode reduces repeat inspection. A lexicon can make rendering consistent, but each voice and language configuration should be tested because support differs across engines. Treat number-to-speech conversion as a formatting problem with a reviewed output, not a creative writing task. The additional lexicon and approval work is small compared with correcting a released audio guide in several languages and replacing its captions and transcript.",
        "mistakes": ["Do not assume a spelling gives the approved pronunciation.", "Do not read an internal identifier aloud merely because it appears in source data.", "Do not let a pronunciation hint change the measured value."],
        "related": ["prompt-engineering/locale-formatting-structured-values", "prompt-engineering/translation-glossary-placeholder-contract", "prompt-engineering/speech-generation-script-and-direction"],
        "section": applications,
    },
    {
        "slug": "generated-speech-review-and-voice-asset-gate",
        "title": "Generated speech review: check the actual voice asset",
        "summary": "Verify words, clarity, permitted voice choice, and text alternatives before release.",
        "definition": "A rendered speech file is a separate artifact from its script. A release gate should compare approved words with the audio, listen for clipped or mispronounced phrases, inspect level and pacing, and confirm that the selected voice asset is approved for the project. The prompt may request a voice style; it cannot establish consent or usage rights for an imitated person's voice. Keep the approved voice identifier and review record outside the prompt. Pair the audio with a corrected transcript, and do not label the transcript final until it matches the released file. If a clip is regenerated, review it again even when the text and settings are unchanged.",
        "case": "The Orin Dial guide passes a text comparison, but the renderer clips the first consonant in 'thirteen' and holds a pause through the phrase 'does not measure time.' The audio is misleading despite a correct transcript. A second candidate sounds like a named public figure because the brief said 'use their voice'; the museum has no approved voice asset for that person. The editor rejects it and selects the project's licensed neutral voice. The release packet stores the chosen asset hash, script version, pronunciation guide, transcript, listening notes, and reviewer's decision. A fresh render gets a fresh check.",
        "sample": "Gate A: approved script vs rendered speech.\nGate B: listen to first/last words, numbers, names, pauses, level.\nGate C: voice asset approved for this project.\nGate D: transcript matches released audio hash.",
        "cost": "Listening to R renders of duration D costs O(RD) review time, while text checks can be automated but cannot hear clipping or unpleasant pacing. Limit candidate renders with a clear brief and revise only a failing segment when the renderer supports it, then review the assembled result. Store media hashes so captions and transcripts are tied to the file actually released. A rights or permission check is a project record, not a model confidence score. If a voice choice cannot be verified, use an approved alternative rather than describing an unverified imitation as safe.",
        "mistakes": ["Do not substitute a prompt instruction for voice-asset approval.", "Do not accept audio solely because automatic transcription matches the script.", "Do not reuse an old transcript after regenerating the audio."],
        "related": ["prompt-engineering/caption-transcript-evidence-contract", "prompt-engineering/sensitive-output-redaction-gate", "prompt-engineering/prompt-release-artifact-bundle"],
        "section": applications,
    },
    {
        "slug": "video-generation-shot-motion-contract",
        "title": "Video generation prompts: specify one shot's motion and evidence",
        "summary": "Describe subject, action, camera, duration, and approved visual facts separately.",
        "definition": "A video prompt should be a shot contract, not a pile of atmosphere words. Identify the subject and approved reference asset, the action over time, camera motion, framing, duration target, and facts that must remain visible. A reference image may establish composition, but the output can still invent objects or change labels. For explanatory footage, do not rely on generated in-frame text to carry exact instructions or numbers; add verified text in post-production where possible. Keep a shot list with start and end states so the editor can review temporal continuity. A prompt describes intent, not a guarantee that the rendered frames obey geometry or timing.",
        "case": "The museum wants an eight-second clip of the fictional Orin Dial. Its approved photo shows 13 brass markers around a fixed rim. The brief asks for a slow quarter-turn of the camera around the model while the model itself remains still. A draft clip animates the markers as moving clock hands and adds a fourteenth marker. The editor rejects it: both changes contradict the exhibit record. A revised shot uses a locked reference, modest camera movement, no generated on-screen label, and a separate verified overlay. The reviewer inspects the beginning, midpoint, and end, then scans the whole clip for transient extra parts.",
        "sample": "Subject: approved Orin Dial asset; 13 fixed brass markers.\nAction: model remains still; camera makes slow quarter-turn.\nTarget: eight seconds; label added later from verified text.\nReject: moving markers, extra parts, unstable object identity.",
        "cost": "For S shots and F inspected frames per shot, sampled visual review is O(SF), while a full-duration watch costs time proportional to total video length. Sampling can miss a one-frame error, so inspect the whole short clip when exact object details matter. Long or elaborate prompts increase editing and review complexity without making a renderer deterministic. Keep reference asset version, shot prompt, generator settings, clip hash, and rejected reasons together. If exact marker count cannot be verified reliably in generated motion, use conventional footage or graphics for that shot.",
        "mistakes": ["Do not treat a reference image as a guarantee of object fidelity.", "Do not put exact public instructions only in generated in-frame text.", "Do not check a temporal clip from a single still frame."],
        "related": ["prompt-engineering/image-generation-brief-and-review", "prompt-engineering/video-frame-sampling-disclosure", "prompt-engineering/image-region-verification-contract"],
        "section": applications,
    },
    {
        "slug": "generated-video-continuity-and-accessibility-gate",
        "title": "Generated video release: inspect continuity, claims, and alternatives",
        "summary": "Check the assembled sequence, narration sync, captions, and descriptive text.",
        "definition": "A video release gate evaluates the final assembly rather than isolated good-looking shots. Verify that subject identity, object count, camera direction, lighting continuity where relevant, and narration claims remain consistent across cuts. Compare every spoken or displayed fact with the approved brief. Listen for narration shifts after editing and check captions against the final audio timing. Supply a transcript that carries important visual information, and an accessible player where the site supports it. The prompt can draft a shot or transcript, but the editor must inspect the exported file and published player. Record the asset versions used in assembly so a re-rendered clip triggers the right review.",
        "case": "The Orin Dial sequence joins two eight-second shots. Shot A has 13 fixed markers; shot B suddenly shows 12 and reverses the camera side, making the dial appear to turn on its stand. A polished transition cannot hide the contradiction. The editor replaces shot B, then checks that the approved narration still fits the new cut. A caption cue begins half a second before the spoken phrase 'decorative markers,' so it is retimed. The descriptive transcript notes that the camera moves around a stationary model; it does not claim the dial rotates. The release packet names the final export hash and verifies it in the public player.",
        "sample": "Shot A: 13 fixed markers, stationary model.\nShot B: same object; camera continues around it.\nAssembly check: no object-count or motion contradiction.\nAccessibility: final audio captions + visual detail transcript.\nPublish gate: reviewed export hash equals player asset.",
        "cost": "For S shots and C cuts, a continuity pass is O(S+C) comparisons for a short sequence, plus full playback time. Caption alignment adds work proportional to cue count; re-editing a shot can invalidate several cues and descriptive sentences. A visual model can flag candidates for review, but it may miss a brief marker change or describe a convincing yet false object. Keep a change ledger from shot asset to exported sequence, transcript, captions, and player. The total review cost grows with every derivative, which is a reason to lock factual copy and shot order before mass generation.",
        "mistakes": ["Do not approve shots separately without checking the assembled sequence.", "Do not reuse caption timing after changing the cut or narration.", "Do not assume an approved export is the file loaded by the public player."],
        "related": ["prompt-engineering/video-timecode-evidence", "prompt-engineering/caption-transcript-evidence-contract", "prompt-engineering/accessible-output-evaluation-slices"],
        "section": production,
    },
]

paths = ["prompt-engineering/" + spec["slug"] for spec in specs]
assert not set(paths + [project_path, quiz_path]).intersection(lookup)
titles = {entry["path"]: entry["title"] for entry in entries}
titles.update({path: spec["title"] for path, spec in zip(paths, specs)})
titles[project_path] = "Project: release an audio and video guide for a fictional exhibit"
titles[quiz_path] = "Generated speech and video prompt decisions"


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
                 subject=subject, difficulty="Advanced", tags=["prompt engineering", "generated media"],
                 sort_order=29200 + order, status="published", published_at=stamp,
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

project_connections = paths + ["prompt-engineering/image-generation-brief-and-review", "prompt-engineering/caption-transcript-evidence-contract", "prompt-engineering/prompt-release-artifact-bundle", quiz_path]
project_body = (
    "<p>Prepare an audio and video guide for the fictional Orin Dial exhibit. The approved exhibit record states that the model is 47 centimeters tall, has 13 fixed brass markers, and does not measure time. The name is spoken 'OR-in.' The deliverable is a review packet for a short narration and two eight-second video shots, not an instruction to publish an uninspected generation. Keep the factual script, delivery direction, voice choice, reference photograph, shot plan, captions, transcript, and final export as distinct versioned artifacts.</p>"
    "<h2>Lock speech and image facts</h2><p>Write a script that preserves all three approved facts. Record the spoken forms of the name, measurement, and marker count. Exclude internal inventory code XQ-74 from the public narration. Choose a voice asset approved for this project and request a measured pace with one short sentence pause. After rendering, transcribe and listen to the file. Reject any clip that calls the display model a working clock, clips 'thirteen,' or alters 'does not measure time.' Check actual duration and pair the final file with its corrected transcript.</p>"
    "<h2>Build and inspect two shots</h2><p>Shot A uses the approved photograph and a slow camera move around a stationary model. Shot B continues from the same side, with the same 13 fixed markers. Put exact public words in a verified overlay rather than relying on generated text inside the scene. Inspect each clip and the assembled sequence; a polished shot with an extra marker fails. Retiming the assembly requires another caption check. The descriptive transcript states that the camera moves and the model remains still. Compare the final export hash with the asset loaded by the public player, then log review decisions for the audio, video, captions, and transcript.</p>"
    '<pre><code class="language-text">Approved: Orin Dial; 47 cm; 13 fixed brass markers; not a timekeeper.\nSpeech: exact script + approved OR-in reading; listen to rendered file.\nShot A/B: stationary model; continuing camera move; no extra marker.\nAccessibility: captions from final audio; descriptive transcript.\nRelease: reviewed export hash matches player asset.</code></pre>'
    "<h2>Performance and operating cost</h2><p>With R audio renders of duration D, listening is O(RD). For S shots and F sampled frames, sampled visual checking is O(SF), but a short exact-detail clip still needs full playback. Caption work scales with cue count and must repeat after a material edit. Store script, voice, reference photo, prompt, model, clip, transcript, captions, export, and player versions together; otherwise a correct review can attach to the wrong file. If generated video cannot hold the marker count, replace that shot with photographed footage or a controlled graphic instead of multiplying prompt adjectives.</p>"
    "<h3>Common Mistakes</h3><ul><li>Do not mix factual script edits with voice-style revisions.</li><li>Do not approve a video from one attractive still frame.</li><li>Do not publish captions or a transcript tied to an older render.</li></ul>"
    "<h2>Connected lessons</h2>" + links(project_connections))
new_rows.append(article(project_path, titles[project_path], "Review scripted narration, pronunciation, shot continuity, and final accessible media for a fictional exhibit.", project_body, projects, 60, project_connections, kind="project"))

questions = [
    ("What should remain fixed while changing a narration's pace?", "The approved factual script", "The rendered file hash", "The reviewer name", "Delivery direction should not rewrite exhibit facts."),
    ("A request asks for a 34-second voice clip. What proves its duration?", "Measuring the rendered audio", "The requested duration text", "The script version number", "Generation may not match the target time."),
    ("The synthesizer says Orin incorrectly. What belongs in the brief?", "An approved spoken reading checked in the audio", "More atmosphere words", "An unrelated inventory code", "Unusual names need an explicit reading."),
    ("Should internal code XQ-74 be read publicly just because it is in source data?", "No; include only audience-relevant approved content", "Yes, every data field", "Only when the model guesses its meaning", "The narration has a separate content contract."),
    ("Automatic transcription matches the script, but a syllable is clipped. Release?", "No; listen and repair the audio asset", "Yes, text equality proves clarity", "Yes, if the voice is approved", "Text checks cannot hear clipping."),
    ("A prompt requests an imitation of an unapproved named person's voice. What is needed?", "A verified approved voice asset or an approved alternative", "A stronger style prompt", "A confidence score", "The prompt cannot establish voice permission."),
    ("What should a video shot contract specify?", "Subject, motion, camera, target duration, and fixed facts", "Only mood adjectives", "Only a resolution value", "The shot needs a checkable temporal plan."),
    ("A generated shot adds a fourteenth marker. What should happen?", "Reject it against the approved exhibit record", "Publish because motion is smooth", "Change the exhibit facts", "Visual polish does not override object fidelity."),
    ("Why add exact public labels after generation?", "To control wording and verify it separately", "To avoid all accessibility review", "To prove the model's frames are accurate", "Generated in-frame text may not be reliable enough for exact facts."),
    ("Two good-looking shots disagree about marker count. What review finds this?", "Final assembly continuity review", "Checking only the opening frame", "Audio text comparison alone", "Cross-cut facts can diverge."),
    ("A cut changes after captions were timed. What is next?", "Recheck captions against final audio and edit", "Reuse old timing automatically", "Remove the transcript", "The timing contract attaches to the final cut."),
    ("Which file should the public player load?", "The same export hash that passed review", "Any earlier candidate", "The unreviewed newest render", "Review must match the published artifact."),
]
quiz_entry = copy.deepcopy(lookup["quizzes/prompt-engineering-multimodal-evidence"])
quiz_entry.update(id=str(uuid.uuid5(uuid.NAMESPACE_URL, "aitrove:" + quiz_path)),
                  path=quiz_path, title=titles[quiz_path],
                  summary="Test scripted speech, pronunciation, voice review, video shots, and final media checks.",
                  body="<p>Choose the check that keeps generated media faithful to its approved brief and usable in the final player.</p><h2>Lessons</h2>" + links(paths) + "<h2>Project and sections</h2>" + links([project_path, applications, production, quizzes]),
                  sort_order=29270, status="published", published_at=stamp,
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
    (applications, paths[:4], "Generated speech and video briefs", "Lock script facts, pronunciation, voice approval, and shot motion before rendering."),
    (production, paths[4:], "Generated media release review", "Check continuity, captions, transcript, and the actual published asset."),
    (projects, [project_path], "Fictional exhibit media guide", "Release a checked narration and two-shot video sequence."),
    (quizzes, [quiz_path], "Generated media decisions", "Test audio, pronunciation, shots, and final assembly boundaries."),
]:
    hub = lookup[hub_path]
    hub["data"]["modules"].append({"title": title, "summary": summary, "lessons": selected})
    hub["body"] += "<h2>" + html.escape(title) + "</h2><p>" + html.escape(summary) + "</p>" + links(selected + [project_path, quiz_path])
    hub["updated_at"] = stamp

root_hub = lookup[subject_root]
root_hub["body"] += "<h2>Generated speech and video</h2><p>Separate approved words and object facts from delivery style, shot motion, and final media review.</p>" + links(paths + [project_path, quiz_path])
root_hub["updated_at"] = stamp

backlinks = {
    "prompt-engineering/image-generation-brief-and-review": paths[3],
    "prompt-engineering/audio-transcription-uncertainty": paths[0],
    "prompt-engineering/video-timecode-evidence": paths[4],
    "prompt-engineering/video-frame-sampling-disclosure": paths[3],
    "prompt-engineering/caption-transcript-evidence-contract": paths[4],
    "prompt-engineering/accessible-output-evaluation-slices": paths[4],
    "prompt-engineering/prompt-release-artifact-bundle": paths[2],
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
