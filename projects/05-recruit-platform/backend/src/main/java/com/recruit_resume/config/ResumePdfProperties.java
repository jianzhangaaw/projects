package com.recruit_resume.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Data
@Component
@ConfigurationProperties(prefix = "resume.pdf")
public class ResumePdfProperties {

    private long renderTimeoutSeconds = 60;
}
