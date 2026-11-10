<?php
/**
 * Plugin Name: DekhoExams Question Archive
 * Description: Serves published JEE practice records from the DekhoExams content database.
 * Version: 1.0.0
 */
defined('ABSPATH') || exit;
add_action('rest_api_init', function () {
    register_rest_route('dekhoexams/v1', '/archive/(?P<exam>jee-main|jee-advanced)/(?P<kind>q|chapter|paper|meta)', [
        'methods' => 'GET',
        'permission_callback' => '__return_true',
        'args' => ['slug' => ['required' => true, 'validate_callback' => static function ($slug) {
            return is_string($slug) && strlen($slug) <= 1024 && preg_match('~^[a-zA-Z0-9][a-zA-Z0-9./-]*$~D', $slug);
        }]],
        'callback' => static function ($request) {
            global $wpdb;
            $blob = $wpdb->get_var($wpdb->prepare(
                'SELECT body FROM wp_dekho_content_v1 WHERE collection=%s AND kind=%s AND slug=%s',
                $request['exam'], $request['kind'], $request['slug']
            ));
            if ($wpdb->last_error) return new WP_Error('unavailable', 'Archive unavailable.', ['status' => 503]);
            if ($blob === null) return new WP_Error('missing', 'Record unavailable.', ['status' => 404]);
            $decoded = json_decode(gzuncompress($blob));
            if ($decoded === null) return new WP_Error('invalid', 'Archive unavailable.', ['status' => 503]);
            $response = rest_ensure_response($decoded);
            $response->header('Cache-Control', 'public, max-age=300');
            $response->header('X-Robots-Tag', 'noindex');
            return $response;
        }
    ]);
});
