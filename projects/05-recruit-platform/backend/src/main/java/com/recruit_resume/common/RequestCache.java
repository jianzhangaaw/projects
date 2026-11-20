package com.recruit_resume.common;

import java.util.HashMap;
import java.util.Map;

/**
 * 请求级缓存。
 *
 * <p>一次请求里反复取同一条数据（目前只有「当前学生资料」）不该反复查库。
 * 这里用 ThreadLocal 按 key 存结果，生命周期严格等于一次 HTTP 请求。
 *
 * <p>清理点只有一个：{@link RequestLoggingFilter} 的 finally。它包住所有请求，
 * 不依赖 MVC 拦截器是否被命中，也不依赖 Controller 是否抛异常。
 */
public final class RequestCache {

    private static final ThreadLocal<Map<String, Object>> CACHE = new ThreadLocal<>();

    private RequestCache() {
    }

    /** 取缓存；不存在或类型不符都返回 null（类型不符说明 key 撞了，按未命中处理）。 */
    public static <T> T get(String key, Class<T> type) {
        Map<String, Object> cache = CACHE.get();
        if (cache == null) {
            return null;
        }
        Object value = cache.get(key);
        return type.isInstance(value) ? type.cast(value) : null;
    }

    public static void put(String key, Object value) {
        Map<String, Object> cache = CACHE.get();
        if (cache == null) {
            cache = new HashMap<>();
            CACHE.set(cache);
        }
        cache.put(key, value);
    }

    /** 请求结束清理。线程池复用线程时不清理，下一个请求会读到上一个请求的数据。 */
    public static void clear() {
        CACHE.remove();
    }
}
