package com.recruit_resume.config;

import com.recruit_resume.security.JwtAuthInterceptor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebMvcConfig implements WebMvcConfigurer {

    private final JwtAuthInterceptor jwtAuthInterceptor;
    private final String[] allowedOrigins;

    public WebMvcConfig(
            JwtAuthInterceptor jwtAuthInterceptor,
            @Value("${cors.allowed-origins:http://localhost:5173,http://127.0.0.1:5173}") String[] allowedOrigins
    ) {
        this.jwtAuthInterceptor = jwtAuthInterceptor;
        this.allowedOrigins = allowedOrigins;
    }

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        // 原来写的是 allowedOriginPatterns("*") + allowCredentials(true)，等于允许任意站点带凭证请求。
        // 现在只能来自配置里列出的来源；部署时用 CORS_ALLOWED_ORIGINS 环境变量覆盖。
        registry.addMapping("/**")
                .allowedOrigins(allowedOrigins)
                .allowedMethods("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
                .allowedHeaders("*")
                .allowCredentials(true)
                .maxAge(3600);
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(jwtAuthInterceptor)
                .addPathPatterns("/api/**")
                .excludePathPatterns(
                        "/api/auth/login",
                        "/api/auth/register",
                        "/api/jobs/published"
                );
    }
}
