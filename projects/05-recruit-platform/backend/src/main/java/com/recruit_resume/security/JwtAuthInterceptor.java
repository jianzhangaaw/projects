package com.recruit_resume.security;

import com.recruit_resume.common.BusinessException;
import com.recruit_resume.common.ResultCode;
import io.jsonwebtoken.JwtException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.servlet.HandlerInterceptor;

@Slf4j
@Component
public class JwtAuthInterceptor implements HandlerInterceptor {

    private static final String BEARER_PREFIX = "Bearer ";

    private final JwtTokenProvider jwtTokenProvider;

    public JwtAuthInterceptor(JwtTokenProvider jwtTokenProvider) {
        this.jwtTokenProvider = jwtTokenProvider;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        if (HttpMethod.OPTIONS.matches(request.getMethod())) {
            return true;
        }

        log.debug("认证检查: {} {}", request.getMethod(), request.getRequestURI());
        CurrentUser currentUser = parseCurrentUser(request);
        CurrentUserContext.set(currentUser);
        checkRoleAccess(request.getRequestURI(), currentUser);
        return true;
    }

    @Override
    public void afterCompletion(
            HttpServletRequest request,
            HttpServletResponse response,
            Object handler,
            Exception ex
    ) {
        CurrentUserContext.clear();
    }

    private CurrentUser parseCurrentUser(HttpServletRequest request) {
        String authorization = request.getHeader("Authorization");
        if (!StringUtils.hasText(authorization) || !authorization.startsWith(BEARER_PREFIX)) {
            throw new BusinessException(ResultCode.UNAUTHORIZED);
        }
        String token = authorization.substring(BEARER_PREFIX.length()).trim();
        if (!StringUtils.hasText(token)) {
            throw new BusinessException(ResultCode.UNAUTHORIZED);
        }
        try {
            return jwtTokenProvider.parseToken(token);
        } catch (JwtException | IllegalArgumentException ex) {
            log.warn("JWT认证失败 {} {}: {}", request.getMethod(), request.getRequestURI(), ex.getMessage());
            throw new BusinessException(ResultCode.UNAUTHORIZED);
        }
    }

    private void checkRoleAccess(String uri, CurrentUser currentUser) {
        if (uri.startsWith("/api/admin/") && !"ADMIN".equals(currentUser.getRole())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        if (uri.startsWith("/api/student/") && !"STUDENT".equals(currentUser.getRole())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        if (uri.startsWith("/api/company/") && !"COMPANY".equals(currentUser.getRole())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
    }
}
