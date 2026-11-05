"""Add a representation lesson and an interlinked practical-guides section."""
import datetime
import html
import json
from pathlib import Path
import re
import uuid

root = Path(__file__).resolve().parents[1]
fixture = root / 'src/data/fixtures.json'
rows = json.loads(fixture.read_text())
new_paths = {'machine-learning/vector-vs-raster-in-machine-learning'}
rows = [row for row in rows if row['path'] not in new_paths and not row['path'].startswith('guides/')]
by_path = {row['path']: row for row in rows}
stamp = datetime.datetime.now(datetime.UTC).isoformat()

vector_path = 'machine-learning/vector-vs-raster-in-machine-learning'
guide_root = 'guides/how-to-and-shortcuts'
guide_specs = []

def add(path, title, summary, sections, mistakes, related):
    guide_specs.append(dict(path=path, title=title, summary=summary,
                            sections=sections, mistakes=mistakes, related=related))

add('guides/how-to-create-rules-in-gmail',
    'How to create rules in Gmail with filters',
    'Gmail rules are filters: a search condition is paired with an action for matching mail.', [
    ('Create and test a filter', 'On a computer, open Gmail and use Show search options in the search box. Enter a sender, recipient, subject or other condition. Select Search first and inspect the messages that match; a broad condition can catch unrelated conversations. Return to the search options, choose Create filter, select the action and save it. Start with a label or star before using deletion or forwarding.'),
    ('Choose an action deliberately', 'A filter may apply a label, skip the inbox, star, delete or forward matching mail. For a recurring invoice, match the known sender and a stable subject phrase, then label it “Finance review.” Test an invoice and a similarly worded personal message. If the latter matches, narrow the condition. [[guides/how-to-create-labels-in-gmail|Create the label]] before you depend on it for a workflow.'),
    ('Understand timing and exceptions', 'Forwarding from a filter affects new matching messages; it does not retroactively forward the older search results. A reply only receives the same treatment if it matches the rule condition. If a workflow must process existing mail, review the option to apply the filter to matching conversations when creating it, and check the result. Avoid forwarding sensitive mail to an unverified destination.'),
    ('Maintain the rule', 'Reopen Gmail settings, inspect Filters and Blocked Addresses, and edit or delete a stale filter. Keep a short note of the business purpose and expected sender. Review rule overlap if mail appears under several labels or vanishes from the inbox. [[guides/gmail-search-operators|Search operators]] help test exactly what a condition selects.')],
    ['Do not use a broad subject word with Delete it before inspecting matches.', 'Do not assume a forwarding rule moves older mail.', 'Do not confuse a label with a folder that contains the only copy.'],
    ['guides/how-to-create-labels-in-gmail','guides/gmail-search-operators','guides/gmail-keyboard-shortcuts','guides/excel-shortcut-keys'])

add('guides/how-to-create-labels-in-gmail',
    'How to create and organize Gmail labels',
    'A Gmail label is a tag applied to messages; it is not a folder that owns a single copy of each message.', [
    ('Make the label', 'On a computer, find Labels in the left sidebar and select Create new label. Enter a name that describes the work, such as “Supplier renewals,” rather than a person’s current job title. You may nest it under a broader label if the hierarchy helps. Save it, then open a test message and apply the label from the toolbar. Confirm that the message appears when you open the label.'),
    ('Separate manual and automatic use', 'A manually applied label helps file a specific conversation. For incoming messages that follow a stable pattern, create a filter that applies the label. Keep the search condition narrow enough that unrelated mail stays out. [[guides/how-to-create-rules-in-gmail|The filter guide]] covers the preview step and its timing. A label alone does not automatically label future messages from the same sender.'),
    ('Account for conversation behavior', 'With conversation view, a label on an existing message does not necessarily apply to later replies. Check the actual message or conversation after a reply arrives before assuming a rule is broken. The sender cannot see your personal labels. If several labels apply, removing one label does not delete the message; deleting the message affects its presence under all labels.'),
    ('Keep the sidebar usable', 'Review duplicate names, old projects and nested branches every few months. Edit or remove stale labels from the label menu in Gmail, but first inspect any filters that apply them. Decide whether a message should be archived, labeled or both. [[guides/gmail-keyboard-shortcuts|Keyboard actions]] can speed up manual triage after the naming scheme is stable.')],
    ['Do not assume labels are visible to recipients.', 'Do not treat removal of one label as deletion of a message.', 'Do not create near-duplicate labels that fragment one workflow.'],
    ['guides/how-to-create-rules-in-gmail','guides/gmail-keyboard-shortcuts','guides/gmail-search-operators','guides/excel-shortcut-keys'])

add('guides/gmail-keyboard-shortcuts',
    'Gmail keyboard shortcuts for inbox triage',
    'Gmail shortcuts act on the current focus or selected conversation; some require keyboard shortcuts to be enabled.', [
    ('Enable the right mode', 'On a computer, open Settings, then See all settings, and switch Keyboard shortcuts on before saving. Press ? to inspect Gmail’s current shortcut help. If a key does nothing, first check whether the cursor is inside the search box or message editor. Do not assume the same key sequence works in every language, layout or mobile app.'),
    ('Use a small core set', 'C starts a message; / focuses mail search; G then I opens the inbox. J and K move between conversations, O opens the selected conversation, E archives it, and R begins a reply. These are sequential keys where stated, not a simultaneous chord. Start with a harmless test conversation before using destructive actions or a shared mailbox.'),
    ('Protect the selection', 'X selects a conversation, and S stars it. Check which message or conversation is selected before archiving or deleting. Keyboard work is fastest when the inbox has predictable labels and filters; otherwise a shortcut can move a message faster than you can diagnose where it went. [[guides/how-to-create-labels-in-gmail|Label organization]] and [[guides/how-to-create-rules-in-gmail|filters]] handle that structure.'),
    ('Troubleshoot differences', 'If a shortcut collides with a browser extension, use the toolbar or Gmail shortcut help rather than guessing. Teams that share a procedure should document whether shortcuts are enabled and what keyboard layout is assumed. For a new teammate, a one-page set of five safe actions is more reliable than memorizing an entire key list before understanding how conversation selection works.')],
    ['Do not press a mail action while the wrong conversation is selected.', 'Do not assume shortcut mode is already enabled.', 'Do not confuse sequential keys such as G then I with simultaneous keys.'],
    ['guides/how-to-create-rules-in-gmail','guides/how-to-create-labels-in-gmail','guides/gmail-search-operators','guides/excel-shortcut-keys'])

add('guides/gmail-search-operators',
    'Gmail search operators for precise filters',
    'Search operators narrow Gmail results by fields such as sender, subject, date, label and attachments.', [
    ('Start with the intent', 'For an accounts-payable review, decide whether you mean mail from a sender, mail sent to a shared alias, or any conversation containing an invoice. Those are different queries. Add one condition at a time and inspect matches after each change. Search is a diagnostic step before a filter becomes automatic. [[guides/how-to-create-rules-in-gmail|Filter creation]] should come after the result set looks right.'),
    ('Use fielded terms', 'The forms from:, to:, subject:, has:attachment and label: narrow the search to a field or message property. Quoted phrases help when word order matters. A query such as from:billing@vendor.test has:attachment can still return non-invoice files, so add a stable subject or human review when the action is costly. Use a real sender only in your own mailbox; the domain here is a disposable illustration.'),
    ('Check conversations and exclusions', 'Gmail displays conversation threads, while some label and negative-operator tests apply to messages inside them. A thread can appear even when only one message satisfies an exclusion or label condition. Open the thread and inspect the matching message before treating a surprising result as a search failure. Avoid building a destructive rule from a query you have not tested against known counterexamples.'),
    ('Keep searches maintainable', 'A long expression that nobody understands becomes hard to audit when vendors rename addresses or subjects. Store the purpose, a positive test message and a negative test message. Re-run both after changing the query. [[guides/how-to-create-labels-in-gmail|Labels]] can group results without forcing a fragile search to make a permanent decision about every message.')],
    ['Do not assume a returned conversation means every message in it matched.', 'Do not use a broad exclusion as proof that no relevant mail remains.', 'Do not automate deletion before testing counterexamples.'],
    ['guides/how-to-create-rules-in-gmail','guides/how-to-create-labels-in-gmail','guides/gmail-keyboard-shortcuts','guides/how-to-filter-data-in-excel'])

add('guides/excel-shortcut-keys',
    'Excel shortcut keys: a focused Windows and Mac reference',
    'Excel shortcuts depend on platform, keyboard layout and context; a short tested set is more useful than an undifferentiated key dump.', [
    ('Move and select', 'On Windows, Ctrl + Arrow moves to the edge of a data region; Ctrl + Shift + Arrow extends the selection. On Mac, Command + Arrow and Shift + Command + Arrow cover the corresponding navigation pattern. Test the command in a disposable sheet because blanks and merged cells affect the stopping point. Do not use a large selection in a destructive command without checking its borders.'),
    ('Edit and format', 'Ctrl + 1 opens Format Cells on Windows; Command + 1 does so on Mac. Ctrl + T creates a table on Windows, while Command + T is available on Mac. F2 edits an active cell in Excel, though function keys on some laptops need an Fn modifier. A table gives filters and structured ranges a clearer boundary. [[guides/how-to-filter-data-in-excel|Filtering]] still requires the headers and data types to be checked.'),
    ('Work with formulas and filters', 'On Windows, F4 cycles reference forms when a cell reference is selected in a formula. Ctrl + Shift + L toggles a filter. On Mac, Command + Shift + F or Ctrl + Shift + L can add or remove a filter. Confirm the active application and cell mode first; browser, operating-system and Excel shortcut handlers can compete for the same keys.'),
    ('Build a personal set', 'Choose five repeated tasks: move to an edge, select a range, edit a cell, format it and filter a table. Practice each in an expendable workbook and write down the platform that was tested. [[guides/google-sheets-shortcut-keys|Sheets shortcuts]] overlap in places but are not a drop-in substitute for Excel, especially for function keys and browser commands.')],
    ['Do not assume Windows and Mac modifiers are interchangeable.', 'Do not use F4 reference cycling unless the cursor is on a formula reference.', 'Do not apply a filter to an incomplete or headerless range.'],
    ['guides/how-to-filter-data-in-excel','guides/how-to-freeze-panes-in-excel','guides/google-sheets-shortcut-keys','guides/gmail-keyboard-shortcuts'])

add('guides/how-to-freeze-panes-in-excel',
    'How to freeze rows and columns in Excel',
    'Freeze Panes keeps selected header rows or identifying columns visible while the rest of a worksheet scrolls.', [
    ('Pick the boundary cell', 'Select the cell immediately below the rows and immediately right of the columns you want to keep visible. To retain rows 1 and 2 plus columns A and B, select C3. Then open View, Freeze Panes and Freeze Panes. Excel freezes everything above and left of the active cell, so a mistaken selection can retain a much larger region than intended.'),
    ('Use the simple variants', 'If you only need the first row or first column, use the dedicated Freeze Top Row or Freeze First Column action where it appears in your Excel version. Scroll far enough to confirm the intended headers remain visible. If you inherited a workbook, unfreeze the current panes before choosing a new boundary so the outcome is easy to understand.'),
    ('Separate view from data', 'Freezing does not sort, protect or lock the values in cells. It changes how the sheet is viewed while scrolling. A collaborator may see a different scroll position, and a printed sheet needs its own print-title settings if headers must repeat on paper. [[guides/how-to-filter-data-in-excel|Filtering]] is a separate operation that hides rows by condition rather than holding headers in place.'),
    ('Check the workbook', 'Use a sheet with 47 records and two header rows. Freeze at C3, scroll to row 40 and column H, and verify both header rows and the first two identifier columns remain visible. Unfreeze from View when the task changes. If the result seems wrong, inspect the selected cell and any existing split panes before repeating the command.')],
    ['Do not select the last header cell; select the cell below and right of the retained area.', 'Do not confuse freezing with cell protection.', 'Do not assume frozen headers automatically repeat when printed.'],
    ['guides/excel-shortcut-keys','guides/how-to-filter-data-in-excel','guides/google-sheets-shortcut-keys','guides/how-to-create-rules-in-gmail'])

add('guides/how-to-filter-data-in-excel',
    'How to filter data in Excel without losing rows',
    'An Excel filter changes which rows are displayed; it does not delete the rows that fail the condition.', [
    ('Prepare a clean range', 'Give every column a distinct header and keep the data range contiguous. Select a cell inside the range or turn the range into an Excel table. Use Data, then Filter; the header cells acquire filter controls. If an empty row divides the data, Excel may infer a smaller range than intended. Check the count of records before making decisions from the filtered view.'),
    ('Apply one condition at a time', 'Open a column’s filter menu and choose values or a text, number or date condition. For a receipt ledger, filter Status to “Pending” and then filter Due date to the coming week. Read the visible row count and inspect a few records against the expected condition. [[guides/excel-shortcut-keys|The filter shortcut]] can toggle controls, but it does not repair an incorrect range.'),
    ('Clear and verify', 'Clear a column filter or use the Data tab to clear all filters when you need the complete sheet again. A filtered row is hidden from view, not removed from the workbook. Before copying, exporting or summing a subset, decide whether the operation should include hidden rows; formulas and selection behavior depend on the function or command used.'),
    ('Avoid silent mistakes', 'Check for mixed text and numeric values in the same column, dates imported as text, blank header cells and merged cells. If a filter appears to skip records, first inspect the actual range and data types. [[guides/how-to-freeze-panes-in-excel|Freezing headers]] improves orientation while reviewing long filtered lists, but it does not change the filter result.')],
    ['Do not assume hidden rows have been deleted.', 'Do not trust an automatically inferred range when blank rows split the data.', 'Do not interpret text-formatted dates as chronological dates.'],
    ['guides/excel-shortcut-keys','guides/how-to-freeze-panes-in-excel','guides/google-sheets-shortcut-keys','guides/gmail-search-operators'])

add('guides/google-sheets-shortcut-keys',
    'Google Sheets shortcut keys for editing and review',
    'Sheets uses browser-based keyboard commands whose modifier keys differ by operating system and may be intercepted by the browser.', [
    ('Open the current list', 'Press Ctrl + / on Windows or ChromeOS, or Command + / on Mac, to view the shortcut list inside Sheets. That list is safer than memorizing a command from another spreadsheet product because keyboard layout and browser can change behavior. Use the tool finder—Alt + / on Windows or Option + / on Mac—when you know the action name but not its key sequence.'),
    ('Edit a selected range', 'Ctrl + C and Ctrl + V copy and paste on Windows; Command + C and Command + V do so on Mac. Paste values only uses Ctrl + Shift + V on Windows and Command + Shift + V on Mac. Test a formula cell and a formatted cell to see what is retained. Fill down uses Ctrl + D or Command + D for a selected range; review relative references before applying it to many rows.'),
    ('Select carefully', 'Ctrl + Space selects a column and Shift + Space selects a row in the documented desktop shortcuts. With large sheets, a whole-column selection can affect far more cells than expected. Use the shortcut list to check platform-specific selection and undo commands. [[guides/excel-shortcut-keys|Excel shortcuts]] may look similar, but do not assume every Excel chord has the same result in Sheets.'),
    ('Resolve conflicts', 'If a shortcut triggers a browser action or an input method, use Sheets menus or the tool finder and note the environment where the conflict occurs. Compatible spreadsheet shortcuts can be enabled from Sheets’ keyboard shortcut window, but that setting changes the meaning of some commands. Teach a team one tested set rather than mixing defaults and compatibility mode without saying which is active.')],
    ['Do not mix default and compatible-shortcut modes without checking the current setting.', 'Do not paste formulas when the task requires fixed values.', 'Do not apply fill-down to a selection whose formulas have not been checked.'],
    ['guides/excel-shortcut-keys','guides/how-to-filter-data-in-excel','guides/how-to-freeze-panes-in-excel','guides/gmail-keyboard-shortcuts'])

assert len(guide_specs) == 8
titles = {path: row['title'] for path, row in by_path.items()}
titles.update({item['path']: item['title'] for item in guide_specs})
titles[guide_root] = 'How-to Guides & Shortcut Keys'
titles[vector_path] = 'Vector vs raster in machine learning: geometry, pixels and feature vectors'

def linked(value):
    return re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]',
                  lambda match: '<a href="/' + match[1] + '">' + match[2] + '</a>',
                  html.escape(value))

def link_list(paths):
    return '<ul>' + ''.join('<li><a href="/' + path + '">' + html.escape(titles[path]) + '</a></li>'
                            for path in paths) + '</ul>'

def entry(path, title, summary, body, entry_type, category, subject, order, data):
    return dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://aitrove.in/' + path)),
                type=entry_type, path=path, title=title, summary=summary, body=body,
                category=category, subject=subject, difficulty='Beginner', tags=[subject, 'guide'],
                data=data, potd_date=None, featured=False, sort_order=order, status='published',
                published_at=stamp, created_at=stamp, updated_at=stamp)

vector_summary = ('Vector geometry describes shapes with coordinates; raster data records values in a fixed grid. '
                  'An ML feature vector is a third concept: an ordered list of numeric features.')
vector_sections = [
    ('Separate the three meanings', 'A delivery-zone boundary represented by polygon coordinates is vector geometry. A satellite tile or scanned receipt is raster data because values occupy rows and columns of cells. In machine learning, a feature vector is an ordered numeric array for one example; it can be built from either source. The word “vector” therefore needs context. [[geospatial-analytics/location-unit-and-coordinate-contract|Location contracts]] specify units and coordinate systems for geometry, while a feature vector specifies feature order and transformation.'),
    ('Choose a representation for the task', 'Use vector geometry when exact boundaries, vertices and topology matter, such as whether a pickup point lies inside a service zone. Use a raster for dense measurements across space, such as image pixels, temperature cells or a segmentation mask. In a receipt model, a rectangular field annotation may be stored as four coordinates, while the scanned page and pixel-level target mask are rasters. [[computer-vision/annotation-geometry-and-quality|Annotation geometry]] must remain aligned with the image revision.'),
    ('Understand conversion loss', 'Rasterizing a polygon assigns each cell a class or value at a selected resolution. Narrow edges can disappear and boundary positions shift when cell size changes. Vectorizing a mask approximates its pixel boundary with coordinates, but cannot recover detail that was never sampled. Save resolution, origin, coordinate frame and class semantics with the output. A model trained at one scale may misread masks generated at another; resizing labels requires an appropriate categorical interpolation method.'),
    ('Apply it in an ML pipeline', 'For a warehouse coverage model, retain service areas as vector polygons for eligibility tests, then sample an aligned raster of demand density to create image-like features. For a scanned invoice, store the document raster, text-box coordinates and field values separately. A numerical feature vector might combine OCR confidence, page dimensions and merchant history; it is not a vector drawing. [[machine-learning/prediction-time-feature-availability|Feature availability]] still determines whether each value may enter a real prediction.'),
    ('Check one concrete box', 'In a 47-column by 29-row receipt image, a half-open box from x=8 to x=31 and y=6 to y=19 covers 23 columns and 13 rows, or 299 pixels. Convert it to a mask, then verify the count and alignment against the image. If a resized image is used, transform the box coordinates first; copying the old box onto the new grid silently corrupts the training label.')
]
vector_code = '''def box_to_mask(left, top, right, bottom, width, height):
    if min(width, height) < 0 or left > right or top > bottom:
        raise ValueError("invalid image or box")
    mask = [[0] * width for _ in range(height)]
    x_start, x_end = max(0, min(width, left)), max(0, min(width, right))
    y_start, y_end = max(0, min(height, top)), max(0, min(height, bottom))
    for pixel_row in range(y_start, y_end):
        mask[pixel_row][x_start:x_end] = [1] * max(0, x_end - x_start)
    return mask

receipt_mask = box_to_mask(8, 6, 31, 19, 47, 29)
assert sum(map(sum, receipt_mask)) == 299'''
vector_cost = ('Allocating a W-by-H mask costs O(W × H) time and space; writing a bounded box adds O(A) work for A covered cells. '
               'A sparse polygon uses space proportional to its vertices, but point-in-polygon tests and rasterization have their own costs. '
               'At large image sizes, tile or stream masks instead of allocating full-resolution copies for every annotation.')
vector_mistakes = [
    'Do not call a numerical feature vector a vector graphic.',
    'Do not compare raster masks without matching resolution, origin and class meaning.',
    'Do not assume rasterization preserves a narrow boundary exactly.',
]
vector_related = ['computer-vision/annotation-geometry-and-quality',
                  'geospatial-analytics/location-unit-and-coordinate-contract',
                  'geospatial-analytics/geometry-validation-and-spatial-joins',
                  'machine-learning/prediction-time-feature-availability',
                  'data-visualization/distribution-and-outlier-displays']
vector_body = '<p>' + html.escape(vector_summary) + '</p>'
for heading, paragraph in vector_sections:
    vector_body += '<h2>' + html.escape(heading) + '</h2><p>' + linked(paragraph) + '</p>'
vector_body += ('<h2>Implementation</h2><pre><code class="language-python">' + html.escape(vector_code)
                + '</code></pre><h2>Performance and operating cost</h2><p>' + html.escape(vector_cost)
                + '</p><h3>Common Mistakes</h3><ul>'
                + ''.join('<li>' + html.escape(mistake) + '</li>' for mistake in vector_mistakes)
                + '</ul><h2>Read next</h2>' + link_list(vector_related))
ml_root = 'machine-learning/machine-learning-tutorial'
vector_row = entry(vector_path, titles[vector_path], vector_summary, vector_body,
                   'article', 'AI & Data', 'machine-learning', 11100,
                   {'kind':'tutorial', 'subject_root':ml_root, 'section_path':ml_root,
                    'content_format':'html', 'seo_ready':True, 'author_path':'authors/aitrove-editorial',
                    'reading_minutes':6, 'verification_suite':'Python syntax and fixture assertion',
                    'related':[{'path':path,'title':titles[path]} for path in vector_related]})
rows.append(vector_row)
by_path[vector_path] = vector_row

groups = [
    ('Gmail: organize and find mail', [
        'guides/how-to-create-rules-in-gmail','guides/how-to-create-labels-in-gmail',
        'guides/gmail-keyboard-shortcuts','guides/gmail-search-operators']),
    ('Spreadsheets: edit and inspect', [
        'guides/excel-shortcut-keys','guides/how-to-freeze-panes-in-excel',
        'guides/how-to-filter-data-in-excel','guides/google-sheets-shortcut-keys']),
]
modules = [{'title':name, 'summary':'Use a tested procedure and check its edge cases.', 'lessons':paths}
           for name, paths in groups]
hub_summary = 'Short procedures and keyboard references for common Gmail and spreadsheet work, grouped by task.'
hub_body = '<p>' + hub_summary + '</p>'
for group_name, paths in groups:
    hub_body += '<h2>' + html.escape(group_name) + '</h2>' + link_list(paths)
hub_body += ('<h2>Related learning</h2>' + link_list([
    'websites-apps/software-and-tools-a-to-z-list',
    'data-visualization/data-visualization-tutorial', vector_path]))
hub = entry(guide_root, titles[guide_root], hub_summary, hub_body,
            'subject', 'Tools', 'guides', 11400,
            {'modules':modules, 'subject_root':guide_root, 'section_path':guide_root,
             'resource_tabs':[{'title':'How-to & Shortcuts','path':guide_root}],
             'content_format':'html', 'seo_ready':True,
             'author_path':'authors/aitrove-editorial'})
rows.append(hub)
by_path[guide_root] = hub

for index, item in enumerate(guide_specs):
    body = '<p>' + html.escape(item['summary']) + '</p>'
    for heading, paragraph in item['sections']:
        body += '<h2>' + html.escape(heading) + '</h2><p>' + linked(paragraph) + '</p>'
    body += ('<h3>Common Mistakes</h3><ul>'
             + ''.join('<li>' + html.escape(mistake) + '</li>' for mistake in item['mistakes'])
             + '</ul><h2>Read next</h2>' + link_list(item['related']))
    article = entry(item['path'], item['title'], item['summary'], body,
                    'article', 'Tools', 'guides', 11410 + index,
                    {'kind':'how-to', 'subject_root':guide_root, 'section_path':guide_root,
                     'content_format':'html', 'seo_ready':True,
                     'author_path':'authors/aitrove-editorial',
                     'reading_minutes':max(2, len(re.sub(r'<[^>]+>', ' ', body).split()) // 180),
                     'related':[{'path':path,'title':titles[path]} for path in item['related']]})
    rows.append(article)
    by_path[item['path']] = article

ml_hub = by_path[ml_root]
foundation = ml_hub['data']['modules'][0]['lessons']
if vector_path not in foundation:
    foundation.append(vector_path)
vector_anchor = '<p><strong>Compare data representations:</strong> <a href="/' + vector_path + '">' + html.escape(titles[vector_path]) + '</a>.</p>'
if vector_anchor not in ml_hub['body']:
    ml_hub['body'] += vector_anchor
ml_hub['updated_at'] = stamp

for source in ['computer-vision/annotation-geometry-and-quality',
               'geospatial-analytics/location-unit-and-coordinate-contract']:
    row = by_path[source]
    anchor = '<p><strong>Compare representations:</strong> <a href="/' + vector_path + '">' + html.escape(titles[vector_path]) + '</a>.</p>'
    if anchor not in row['body']:
        row['body'] += anchor
        row['data']['related'].append({'path':vector_path,'title':titles[vector_path]})
        row['updated_at'] = stamp

software = by_path['websites-apps/software-and-tools-a-to-z-list']
new_module = {'title':'Practical how-to and shortcut keys','lessons':[guide_root]}
if not any(module['title'] == new_module['title'] for module in software['data']['modules']):
    software['data']['modules'].append(new_module)
software_anchor = '<p><strong>Practical guides:</strong> <a href="/' + guide_root + '">' + html.escape(titles[guide_root]) + '</a>.</p>'
if software_anchor not in software['body']:
    software['body'] += software_anchor
software['updated_at'] = stamp

assert len({row['path'] for row in rows}) == len(rows)
fixture.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'new_articles':9, 'new_hubs':1, 'vector_path':vector_path, 'guide_root':guide_root}))
