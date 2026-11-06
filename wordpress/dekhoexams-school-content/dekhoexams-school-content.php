<?php
/**
 * Plugin Name: Dekhoexams School Content
 * Description: Publish reviewed lesson text to the Dekhoexams Cloudflare frontend.
 * Version: 1.0.0
 * Requires PHP: 8.0
 */

if (!defined('ABSPATH')) exit;

const DEKHO_LESSON_FIELDS = [
    'summary' => 'Summary',
    'keyIdea' => 'Key idea',
    'whyItWorks' => 'Why it works',
    'commonMistake' => 'Common mistake',
    'example' => 'Worked example',
    'steps' => 'Worked steps (one per line)',
    'check' => 'Check your answer',
];

add_action('init', function () {
    register_post_type('dekho_lesson', [
        'labels' => ['name' => 'School lessons', 'singular_name' => 'School lesson'],
        'public' => false,
        'show_ui' => true,
        'show_in_rest' => false,
        'menu_icon' => 'dashicons-welcome-learn-more',
        'supports' => ['title', 'revisions'],
        'map_meta_cap' => true,
    ]);
});

add_action('add_meta_boxes_dekho_lesson', function () {
    add_meta_box('dekho_lesson_details', 'Dekhoexams lesson text', function ($post) {
        wp_nonce_field('dekho_save_lesson', 'dekho_lesson_nonce');
        $id = get_post_meta($post->ID, '_dekho_resource_id', true);
        echo '<p><label for="dekho_resource_id"><strong>Resource ID (for example pp-0001)</strong></label><br>';
        echo '<input class="widefat" id="dekho_resource_id" name="dekho_resource_id" value="' . esc_attr($id) . '" required pattern="pp-[0-9]{4}"></p>';
        echo '<p>Publish to replace the lesson text on the frontend. Practice questions and saved-answer versions remain in the frontend code.</p>';
        foreach (DEKHO_LESSON_FIELDS as $key => $label) {
            $value = get_post_meta($post->ID, '_dekho_' . $key, true);
            echo '<p><label for="dekho_' . esc_attr($key) . '"><strong>' . esc_html($label) . '</strong></label><br>';
            echo '<textarea class="widefat" rows="' . ($key === 'steps' ? 6 : 4) . '" id="dekho_' . esc_attr($key) . '" name="dekho_' . esc_attr($key) . '">' . esc_textarea($value) . '</textarea></p>';
        }
    }, 'dekho_lesson', 'normal', 'high');
});

add_action('save_post_dekho_lesson', function ($post_id) {
    if (!isset($_POST['dekho_lesson_nonce']) || !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['dekho_lesson_nonce'])), 'dekho_save_lesson')) return;
    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) return;
    if (!current_user_can('edit_post', $post_id)) return;
    $id = sanitize_text_field(wp_unslash($_POST['dekho_resource_id'] ?? ''));
    if (!preg_match('/^pp-[0-9]{4}$/', $id)) return;
    update_post_meta($post_id, '_dekho_resource_id', $id);
    foreach (DEKHO_LESSON_FIELDS as $key => $_label) {
        $raw = wp_unslash($_POST['dekho_' . $key] ?? '');
        update_post_meta($post_id, '_dekho_' . $key, sanitize_textarea_field(is_string($raw) ? $raw : ''));
    }
});

add_action('rest_api_init', function () {
    register_rest_route('dekhoexams/v1', '/lesson', [
        'methods' => 'GET',
        'permission_callback' => '__return_true',
        'args' => ['id' => ['required' => true, 'validate_callback' => function ($id) {
            return is_string($id) && (bool) preg_match('/^pp-[0-9]{4}$/', $id);
        }]],
        'callback' => function ($request) {
            $query = new WP_Query([
                'post_type' => 'dekho_lesson', 'post_status' => 'publish',
                'posts_per_page' => 2, 'no_found_rows' => true,
                'meta_query' => [['key' => '_dekho_resource_id', 'value' => $request['id']]],
            ]);
            if (!$query->have_posts()) return new WP_Error('not_found', 'Lesson not found.', ['status' => 404]);
            if (count($query->posts) > 1) return new WP_Error('duplicate_id', 'More than one published lesson uses this resource ID.', ['status' => 409]);
            $post = $query->posts[0];
            $lesson = ['title' => get_the_title($post)];
            foreach (DEKHO_LESSON_FIELDS as $key => $_label)
                $lesson[$key] = (string) get_post_meta($post->ID, '_dekho_' . $key, true);
            $lesson['steps'] = array_values(array_filter(array_map('trim', explode("\n", $lesson['steps']))));
            foreach (DEKHO_LESSON_FIELDS as $key => $_label)
                if (!$lesson[$key]) return new WP_Error('incomplete_lesson', 'Complete every lesson field before publishing.', ['status' => 422]);
            return rest_ensure_response($lesson);
        },
    ]);
});
