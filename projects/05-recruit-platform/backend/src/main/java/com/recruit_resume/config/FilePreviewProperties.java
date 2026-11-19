package com.recruit_resume.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.nio.file.Path;

@Data
@Component
@ConfigurationProperties(prefix = "file.preview")
public class FilePreviewProperties {

    private String libreOfficePath = "soffice";
    private String cacheDir = Path.of(System.getProperty("java.io.tmpdir"), "recruit-resume-preview").toString();
    private long convertTimeoutSeconds = 60;
}
