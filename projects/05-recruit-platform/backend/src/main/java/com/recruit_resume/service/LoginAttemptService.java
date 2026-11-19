package com.recruit_resume.service;

import com.recruit_resume.common.BusinessException;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.Iterator;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 登录失败计数与临时锁定。
 *
 * <p>按用户名计数，连续失败 5 次锁 15 分钟。放在内存里就够用——校园招聘平台的并发量远低于
 * 需要 Redis 的规模，而且重启清空是可接受的（锁定本身是防御性措施，不是业务数据）。
 *
 * <p>注意这里只按用户名计数、不按 IP：按 IP 会在校园网 NAT 下误伤整栋楼。
 * 代价是攻击者可以换 IP 继续撞，所以它只是「挡住低成本字典」这一层，不是完整方案。
 */
@Service
public class LoginAttemptService {

    private static final int MAX_ATTEMPTS = 5;
    private static final Duration LOCK_DURATION = Duration.ofMinutes(15);
    /** 每处理这么多次失败顺手清理一遍过期记录，避免 Map 无限增长。 */
    private static final long CLEAN_INTERVAL = 100;

    private final Map<String, Attempt> attempts = new ConcurrentHashMap<>();
    private final AtomicLong operations = new AtomicLong();

    private static final class Attempt {
        int failures;
        Instant lockedUntil;
        Instant lastFailure;
    }

    public void assertNotLocked(String username) {
        Attempt attempt = attempts.get(key(username));
        if (attempt == null) {
            return;
        }
        Instant now = Instant.now();
        if (attempt.lockedUntil != null && now.isBefore(attempt.lockedUntil)) {
            long minutes = Math.max(1, Duration.between(now, attempt.lockedUntil).toMinutes() + 1);
            throw new BusinessException("登录失败次数过多，请 " + minutes + " 分钟后再试");
        }
        if (attempt.lockedUntil != null) {
            // 锁定期已过，重新开始计数
            attempts.remove(key(username));
        }
    }

    public void recordFailure(String username) {
        Attempt attempt = attempts.computeIfAbsent(key(username), k -> new Attempt());
        synchronized (attempt) {
            attempt.failures++;
            attempt.lastFailure = Instant.now();
            if (attempt.failures >= MAX_ATTEMPTS) {
                attempt.lockedUntil = Instant.now().plus(LOCK_DURATION);
            }
        }
        if (operations.incrementAndGet() % CLEAN_INTERVAL == 0) {
            cleanUp();
        }
    }

    public void reset(String username) {
        attempts.remove(key(username));
    }

    private void cleanUp() {
        Instant now = Instant.now();
        Iterator<Map.Entry<String, Attempt>> it = attempts.entrySet().iterator();
        while (it.hasNext()) {
            Attempt attempt = it.next().getValue();
            boolean lockExpired = attempt.lockedUntil != null && now.isAfter(attempt.lockedUntil);
            boolean stale = attempt.lockedUntil == null
                    && attempt.lastFailure != null
                    && attempt.lastFailure.isBefore(now.minus(LOCK_DURATION));
            if (lockExpired || stale) {
                it.remove();
            }
        }
    }

    private String key(String username) {
        return username == null ? "" : username.trim().toLowerCase();
    }
}
