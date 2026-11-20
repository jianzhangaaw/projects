package com.recruit_resume.common;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Slf4j
@Component
public class RequestLoggingFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain)
            throws ServletException, IOException {
        String uri = request.getRequestURI();
        // 静态资源与健康检查只过链，不打耗时日志
        boolean quiet = uri.startsWith("/actuator") || uri.startsWith("/static");
        long start = System.currentTimeMillis();
        try {
            filterChain.doFilter(request, response);
        } finally {
            if (!quiet) {
                long elapsed = System.currentTimeMillis() - start;
                int status = response.getStatus();
                if (status >= 400) {
                    log.warn("{} {} -> {} {}ms", request.getMethod(), uri, status, elapsed);
                } else {
                    log.debug("{} {} -> {} {}ms", request.getMethod(), uri, status, elapsed);
                }
            }
            // 请求级缓存必须在这里清：线程池会复用线程，不清就会把上一个请求的学生资料带给下一个请求
            RequestCache.clear();
        }
    }
}
