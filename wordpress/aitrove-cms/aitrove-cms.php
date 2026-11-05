<?php
/**
 * Plugin Name: AITrove Content API
 * Description: WordPress editorial workspace and public API for the AITrove frontend.
 * Version: 0.3.2
 * Requires PHP: 8.0
 */

if (!defined('ABSPATH')) exit;

const AITROVE_TYPES = ['subject', 'article', 'category', 'problem', 'course', 'video', 'event', 'job', 'business', 'page', 'quiz', 'path', 'company', 'author'];
const AITROVE_META = ['type', 'path', 'summary', 'body', 'category', 'subject', 'difficulty', 'tags', 'data', 'potd_date', 'featured', 'sort_order'];

add_action('init', function () {
    register_post_type('aitrove_entry', [
        'labels' => ['name' => 'Learning Content', 'singular_name' => 'Content Entry', 'add_new_item' => 'Add Content Entry'],
        'public' => false,
        'show_ui' => true,
        'show_in_menu' => true,
        'show_in_rest' => false,
        'menu_icon' => 'dashicons-welcome-learn-more',
        'supports' => ['title', 'author', 'revisions'],
        'map_meta_cap' => true,
    ]);
});

function aitrove_path($value) {
    $path = trim(strtolower((string) $value), '/');
    return preg_replace('~[^a-z0-9/_-]~', '', $path);
}

add_action('add_meta_boxes_aitrove_entry', function () {
    add_meta_box('aitrove_details', 'Page details', 'aitrove_details_box', 'aitrove_entry', 'normal', 'high');
});

function aitrove_details_box($post) {
    wp_nonce_field('aitrove_save_entry', 'aitrove_nonce');
    $fields = [
        'type' => ['Template type', 'select'], 'path' => ['Public path (without leading slash)', 'text'],
        'summary' => ['Summary', 'textarea'], 'body' => ['Article body (semantic HTML)', 'textarea'],
        'category' => ['Category', 'text'], 'subject' => ['Subject slug', 'text'],
        'difficulty' => ['Difficulty', 'text'], 'tags' => ['Tags (comma separated)', 'text'],
        'data' => ['Template data (JSON)', 'textarea'], 'potd_date' => ['Problem of the day (YYYY-MM-DD)', 'text'],
        'featured' => ['Featured', 'checkbox'], 'sort_order' => ['Sort order', 'number'],
    ];
    echo '<details><summary><strong>Template data guide</strong></summary><p>All pages share title, path, summary and semantic HTML body. Use template JSON for structured fields:</p><ul><li>Quiz: questions (prompt, options, answer as zero-based index, explanation), duration_minutes.</li><li>Path: steps (title, path, kind), duration.</li><li>Course: syllabus (title, items), lessons (title, module, body), batches (title, schedule, seats), projects, instructor_path.</li><li>Subject: modules (title, summary, lessons as published paths), resource_tabs (title, path), subject_root (main tutorial path), section_path (current section hub). Use a separate subject slug for each section so its sidebar changes. Articles: subject_root and section_path link back to the family and selected section.</li><li>Author: role, expertise. Articles: author_path.</li><li>Company: company, location, industry. Jobs: company, company_path, apply_url.</li><li>Event: problems (published paths), starts_at, ends_at, register_url, agenda.</li><li>Video: video_url, transcript, duration.</li></ul><p>Import the included fixtures with WP-CLI to see complete examples.</p></details>';
    echo '<p>Publish to make this entry visible on the frontend. Drafts stay private. The body accepts sanitized semantic HTML or legacy Markdown; template data holds course modules, problem starter code, event details and similar fields.</p>';
    foreach ($fields as $key => [$label, $kind]) {
        $value = get_post_meta($post->ID, '_aitrove_' . $key, true);
        if ($key === 'data' && $value === '') $value = '{}';
        echo '<p><label for="aitrove_' . esc_attr($key) . '"><strong>' . esc_html($label) . '</strong></label><br>';
        $name = 'aitrove_' . esc_attr($key);
        if ($kind === 'select') {
            echo '<select id="' . $name . '" name="' . $name . '">';
            foreach (AITROVE_TYPES as $type) echo '<option value="' . esc_attr($type) . '" ' . selected($value, $type, false) . '>' . esc_html(ucfirst($type)) . '</option>';
            echo '</select>';
        } elseif ($kind === 'textarea') {
            $rows = $key === 'body' ? 16 : ($key === 'data' ? 8 : 3);
            echo '<textarea class="widefat" rows="' . (int) $rows . '" id="' . $name . '" name="' . $name . '">' . esc_textarea($value) . '</textarea>';
        } elseif ($kind === 'checkbox') {
            echo '<input type="checkbox" id="' . $name . '" name="' . $name . '" value="1" ' . checked($value, '1', false) . '>';
        } else {
            echo '<input class="widefat" type="' . esc_attr($kind) . '" id="' . $name . '" name="' . $name . '" value="' . esc_attr($value) . '">';
        }
        echo '</p>';
    }
}

/** Index template JSON fields used by catalog filters. */
function aitrove_index_data($post_id, $data) {
    // Explicit editorial readiness, separate from WordPress publication status.
    update_post_meta($post_id, '_aitrove_seo_ready', is_array($data) && ($data['seo_ready'] ?? false) === true ? '1' : '0');
    $company = is_array($data) && isset($data['company']) && is_scalar($data['company']) ? sanitize_text_field((string) $data['company']) : '';
    update_post_meta($post_id, '_aitrove_company', $company);
    delete_post_meta($post_id, '_aitrove_companies');
    foreach ((array) ($data['companies'] ?? []) as $name) {
        if (is_scalar($name)) add_post_meta($post_id, '_aitrove_companies', sanitize_text_field((string) $name));
    }
    update_post_meta($post_id, '_aitrove_author_path', aitrove_path($data['author_path'] ?? ''));
}

add_action('save_post_aitrove_entry', function ($post_id) {
    if (!isset($_POST['aitrove_nonce']) || !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['aitrove_nonce'])), 'aitrove_save_entry')) return;
    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) return;
    if (!current_user_can('edit_post', $post_id)) return;
    foreach (AITROVE_META as $key) {
        $raw = isset($_POST['aitrove_' . $key]) ? wp_unslash($_POST['aitrove_' . $key]) : '';
        if (!is_scalar($raw)) $raw = '';
        if ($key === 'featured') $value = $raw === '1' ? '1' : '0';
        elseif ($key === 'sort_order') $value = (string) (int) $raw;
        elseif ($key === 'path') $value = aitrove_path($raw);
        elseif ($key === 'type') $value = in_array($raw, AITROVE_TYPES, true) ? $raw : 'article';
        // The frontend sanitizes HTML and escapes Markdown. Keep angle brackets in
        // code examples; sanitize_textarea_field would erase HTML lessons.
        elseif ($key === 'body') $value = trim((string) $raw);
        elseif ($key === 'data') {
            $parsed = json_decode((string) $raw, true);
            $value = json_last_error() === JSON_ERROR_NONE && is_array($parsed) ? wp_json_encode($parsed, JSON_UNESCAPED_UNICODE) : '{}';
        } else $value = sanitize_text_field($raw);
        update_post_meta($post_id, '_aitrove_' . $key, wp_slash($value));
        if ($key === 'data') aitrove_index_data($post_id, json_decode($value, true) ?: []);
    }
});

function aitrove_entry_response($post, $with_body = true) {
    $get = function ($field) use ($post) { return get_post_meta($post->ID, '_aitrove_' . $field, true); };
    $data = json_decode((string) $get('data'), true);
    $row = [
        'id' => (string) $post->ID,
        'type' => $get('type') ?: 'article',
        'path' => aitrove_path($get('path')),
        'title' => get_the_title($post),
        'summary' => (string) $get('summary'),
        'category' => $get('category') ?: null,
        'subject' => $get('subject') ?: null,
        'difficulty' => $get('difficulty') ?: null,
        'tags' => array_values(array_filter(array_map('trim', explode(',', (string) $get('tags'))))),
        'data' => is_array($data) ? $data : [],
        'potd_date' => $get('potd_date') ?: null,
        'featured' => $get('featured') === '1',
        'sort_order' => (int) $get('sort_order'),
        'status' => 'published',
        'published_at' => get_post_time('c', true, $post),
        'created_at' => get_post_time('c', true, $post),
        'updated_at' => get_post_modified_time('c', true, $post),
    ];
    if ($with_body) $row['body'] = (string) $get('body');
    return $row;
}

add_action('rest_api_init', function () {
    register_rest_route('aitrove/v1', '/entry', [
        'methods' => 'GET', 'permission_callback' => '__return_true',
        'args' => ['path' => ['required' => true, 'sanitize_callback' => 'aitrove_path']],
        'callback' => function ($request) {
            $path = aitrove_path($request['path']);
            if (!$path) return new WP_Error('invalid_path', 'A path is required.', ['status' => 400]);
            $query = new WP_Query(['post_type' => 'aitrove_entry', 'post_status' => 'publish', 'posts_per_page' => 1,
                'meta_query' => [['key' => '_aitrove_path', 'value' => $path, 'compare' => '=']], 'no_found_rows' => true]);
            if (!$query->have_posts()) return new WP_Error('not_found', 'Content not found.', ['status' => 404]);
            return rest_ensure_response(aitrove_entry_response($query->posts[0]));
        },
    ]);
    register_rest_route('aitrove/v1', '/entries', [
        'methods' => 'GET', 'permission_callback' => '__return_true',
        'callback' => function ($request) {
            $limit = min(100, max(1, (int) ($request['limit'] ?: 24)));
            $offset = min(250000, max(0, (int) ($request['offset'] ?: 0)));
            $meta = ['relation' => 'AND'];
            foreach (['type', 'category', 'subject', 'difficulty'] as $key) {
                if (is_scalar($request[$key]) && $request[$key] !== '') $meta[] = ['key' => '_aitrove_' . $key, 'value' => sanitize_text_field((string) $request[$key]), 'compare' => '='];
            }
            if (is_string($request['company']) && $request['company'] !== '') {
                $name = sanitize_text_field($request['company']);
                $meta[] = ['relation' => 'OR', ['key' => '_aitrove_company', 'value' => $name], ['key' => '_aitrove_companies', 'value' => $name]];
            }
            if (is_string($request['author']) && $request['author'] !== '') $meta[] = ['key' => '_aitrove_author_path', 'value' => aitrove_path($request['author'])];
            // Frontend feature flags hide types without deleting editorial records.
            if (is_string($request['exclude_types']) && $request['exclude_types'] !== '') {
                $excluded = array_values(array_intersect(AITROVE_TYPES, explode(',', sanitize_text_field($request['exclude_types']))));
                if ($excluded) $meta[] = ['key' => '_aitrove_type', 'value' => $excluded, 'compare' => 'NOT IN'];
            }
            if ($request['featured'] === 'true') $meta[] = ['key' => '_aitrove_featured', 'value' => '1'];
            if ($request['potd'] === 'true') $meta[] = ['key' => '_aitrove_potd_date', 'value' => '', 'compare' => '!='];
            if (is_string($request['paths']) && $request['paths'] !== '') {
                $paths = array_slice(array_map('aitrove_path', explode(',', (string) $request['paths'])), 0, 100);
                $meta[] = ['key' => '_aitrove_path', 'value' => $paths, 'compare' => 'IN'];
            }
            $args = ['post_type' => 'aitrove_entry', 'post_status' => 'publish', 'posts_per_page' => $limit, 'offset' => $offset, 'meta_query' => $meta];
            if (is_scalar($request['q']) && $request['q'] !== '') $args['s'] = sanitize_text_field((string) $request['q']);
            if ($request['potd'] === 'true') {
                $args['meta_key'] = '_aitrove_potd_date'; $args['orderby'] = 'meta_value'; $args['order'] = 'DESC';
            } else {
                $args['meta_key'] = '_aitrove_sort_order'; $args['orderby'] = ['meta_value_num' => 'ASC', 'date' => 'DESC'];
            }
            $query = new WP_Query($args);
            return rest_ensure_response(['items' => array_map(function ($post) { return aitrove_entry_response($post, false); }, $query->posts), 'total' => (int) $query->found_posts, 'error' => null]);
        },
    ]);
});

/** Import preview records from hPanel/WordPress without shell access. */
add_action('admin_menu', function () {
    add_submenu_page('edit.php?post_type=aitrove_entry', 'Import AITrove content', 'Import content', 'manage_options', 'aitrove-import', 'aitrove_import_screen');
});
function aitrove_import_screen() {
    if (!current_user_can('manage_options')) return;
    echo '<div class="wrap"><h1>Import AITrove content</h1><p>Import or update entries by their public path. Existing entries are preserved; matching paths are updated. Use the preview JSON only on this new preview site.</p>';
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        check_admin_referer('aitrove_import');
        $file = $_FILES['aitrove_json'] ?? [];
        if (($file['error'] ?? UPLOAD_ERR_NO_FILE) !== UPLOAD_ERR_OK || ($file['size'] ?? 0) > 8 * 1024 * 1024 || !is_uploaded_file($file['tmp_name'] ?? '')) {
            echo '<div class="notice notice-error"><p>Choose a valid JSON file smaller than 8 MB.</p></div>';
        } else {
            $rows = json_decode(file_get_contents($file['tmp_name']), true);
            if (!is_array($rows) || (count($rows) > 0 && array_keys($rows) !== range(0, count($rows) - 1)) || count($rows) > 1000) {
                echo '<div class="notice notice-error"><p>Expected a JSON array with up to 1,000 entries.</p></div>';
            } else {
                $count = 0; $failed = 0;
                foreach ($rows as $row) {
                    if (!is_array($row)) { $failed++; continue; }
                    $path = aitrove_path($row['path'] ?? '');
                    if (!$path || !in_array($row['type'] ?? '', AITROVE_TYPES, true) || !is_array($row['data'] ?? [])) { $failed++; continue; }
                    $existing = get_posts(['post_type' => 'aitrove_entry', 'post_status' => ['publish', 'draft', 'pending', 'private'], 'posts_per_page' => 1, 'meta_query' => [['key' => '_aitrove_path', 'value' => $path]]]);
                    $publish = isset($_POST['aitrove_publish']) && ($row['status'] ?? '') === 'published';
                    $id = wp_insert_post(['ID' => $existing ? $existing[0]->ID : 0, 'post_type' => 'aitrove_entry', 'post_title' => sanitize_text_field($row['title'] ?? $path), 'post_status' => $publish ? 'publish' : 'draft'], true);
                    if (is_wp_error($id)) { $failed++; continue; }
                    foreach (AITROVE_META as $key) {
                        $value = $row[$key] ?? '';
                        if ($key === 'tags') $value = implode(',', array_map('sanitize_text_field', (array) $value));
                        if ($key === 'data') $value = wp_json_encode($value, JSON_UNESCAPED_UNICODE);
                        if ($key === 'featured') $value = $value ? '1' : '0';
                        if (is_array($value)) $value = '';
                        update_post_meta($id, '_aitrove_' . $key, wp_slash($value));
                    }
                    aitrove_index_data($id, (array) ($row['data'] ?? [])); $count++;
                }
                echo '<div class="notice notice-success"><p>Imported or updated ' . (int) $count . ' entries. Skipped/failed: ' . (int) $failed . '.</p></div>';
            }
        }
    }
    echo '<form method="post" enctype="multipart/form-data">'; wp_nonce_field('aitrove_import');
    echo '<p><label for="aitrove-json">Content JSON</label><br><input id="aitrove-json" name="aitrove_json" type="file" accept=".json,application/json" required></p><p><label><input type="checkbox" name="aitrove_publish" value="1"> Publish entries marked published in the file (otherwise import as drafts)</label></p>';
    submit_button('Import content'); echo '</form></div>';
}

if (defined('WP_CLI') && WP_CLI) {
    WP_CLI::add_command('aitrove import', function ($args) {
        $file = $args[0] ?? '';
        if (!$file || !is_readable($file)) WP_CLI::error('Pass a readable JSON file.');
        $rows = json_decode(file_get_contents($file), true);
        if (!is_array($rows)) WP_CLI::error('Expected a JSON array.');
        $count = 0;
        foreach ($rows as $row) {
            $path = aitrove_path($row['path'] ?? '');
            if (!$path || !in_array($row['type'] ?? '', AITROVE_TYPES, true)) continue;
            $existing = get_posts(['post_type' => 'aitrove_entry', 'post_status' => ['publish', 'draft'], 'posts_per_page' => 1,
                'meta_query' => [['key' => '_aitrove_path', 'value' => $path]]]);
            $post_id = wp_insert_post(['ID' => $existing ? $existing[0]->ID : 0, 'post_type' => 'aitrove_entry',
                'post_title' => sanitize_text_field($row['title'] ?? $path), 'post_status' => ($row['status'] ?? 'draft') === 'published' ? 'publish' : 'draft'], true);
            if (is_wp_error($post_id)) WP_CLI::warning($path . ': ' . $post_id->get_error_message());
            else {
                foreach (AITROVE_META as $key) {
                    $value = $row[$key] ?? '';
                    if ($key === 'tags') $value = implode(',', (array) $value);
                    if ($key === 'data') $value = wp_json_encode($value, JSON_UNESCAPED_UNICODE);
                    if ($key === 'featured') $value = $value ? '1' : '0';
                    update_post_meta($post_id, '_aitrove_' . $key, wp_slash($value));
                }
                aitrove_index_data($post_id, (array) ($row['data'] ?? []));
                $count++;
            }
        }
        WP_CLI::success("Imported or updated {$count} entries.");
    });
}


/** Metadata-only published content pages for the frontend sitemap. */
add_action('rest_api_init', function () {
    register_rest_route('aitrove/v1', '/sitemap-entries', [
        'methods' => 'GET', 'permission_callback' => '__return_true',
        'args' => [
            'page' => ['default' => 1, 'validate_callback' => function ($v) { return filter_var($v, FILTER_VALIDATE_INT) !== false && (int) $v >= 1 && (int) $v <= 5000; }],
            'per_page' => ['default' => 1000, 'validate_callback' => function ($v) { return filter_var($v, FILTER_VALIDATE_INT) !== false && (int) $v >= 1 && (int) $v <= 1000; }],
        ],
        'callback' => function ($request) {
            do_action('litespeed_control_set_nocache', 'Sitemap metadata changes with editorial publication.');
            $page = (int) $request['page']; $limit = (int) $request['per_page'];
            $query = new WP_Query([
                'post_type' => 'aitrove_entry', 'post_status' => 'publish',
                'posts_per_page' => $limit, 'paged' => $page,
                // Match the path order of the frontend snapshot when a CMS request falls back.
                'meta_key' => '_aitrove_path', 'orderby' => 'meta_value', 'order' => 'ASC',
                'meta_query' => [
                    'relation' => 'AND',
                    ['key' => '_aitrove_seo_ready', 'value' => '1'],
                    ['key' => '_aitrove_type', 'value' => 'course', 'compare' => '!='],
                ],
            ]);
            if ((int) $query->found_posts > 5000 * $limit) return new WP_Error('sitemap_capacity', 'Sitemap pagination capacity exceeded; partition metadata before publishing.', ['status' => 503]);
            $items = [];
            foreach ($query->posts as $post) {
                $items[] = [
                    'path' => aitrove_path(get_post_meta($post->ID, '_aitrove_path', true)),
                    'type' => get_post_meta($post->ID, '_aitrove_type', true) ?: 'article',
                    'status' => 'published', 'data' => ['seo_ready' => true],
                    'updated_at' => get_post_modified_time('c', true, $post),
                ];
            }
            return rest_ensure_response(['items' => $items, 'total' => (int) $query->found_posts, 'page' => $page, 'per_page' => $limit]);
        },
    ]);
});
