<?php
/**
 * Plugin Name: 2bkin Rank Math REST meta
 * Description: Mở các field SEO của Rank Math qua REST API để pipeline đăng bài set được focus keyword / title / description.
 *
 * Cài: copy file này vào wp-content/mu-plugins/ (tạo thư mục nếu chưa có) — tự kích hoạt.
 * Yêu cầu: đã cài plugin Rank Math SEO (free).
 */
add_action('init', function () {
    $keys = ['rank_math_focus_keyword', 'rank_math_title', 'rank_math_description'];
    foreach ($keys as $key) {
        register_post_meta('post', $key, [
            'type'          => 'string',
            'single'        => true,
            'show_in_rest'  => true,
            'auth_callback' => function () {
                return current_user_can('edit_posts');
            },
        ]);
    }
});
