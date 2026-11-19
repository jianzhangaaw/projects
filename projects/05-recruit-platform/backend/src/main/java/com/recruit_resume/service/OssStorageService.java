package com.recruit_resume.service;

import com.aliyun.oss.OSS;
import com.aliyun.oss.model.ObjectMetadata;
import com.recruit_resume.config.OssProperties;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.IOException;
import java.time.LocalDate;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.UUID;

@Slf4j
@Service
public class OssStorageService {

    private final OSS ossClient;
    private final OssProperties properties;

    public OssStorageService(ObjectProvider<OSS> ossClientProvider, OssProperties properties) {
        this.ossClient = ossClientProvider.getIfAvailable();
        this.properties = properties;
    }

    public String upload(MultipartFile file) throws IOException {
        String objectName = objectName(file.getOriginalFilename());
        if (ossAvailable()) {
            try {
                ossClient.putObject(properties.getBucketName(), objectName, file.getInputStream());
                return ossUrl(objectName);
            } catch (RuntimeException ex) {
                log.warn("OSS upload failed, falling back to local file storage: {}", ex.getMessage());
            }
        }

        Path localFile = localPath(objectName);
        Files.createDirectories(localFile.getParent());
        Files.copy(file.getInputStream(), localFile, StandardCopyOption.REPLACE_EXISTING);
        return localFile.toUri().toString();
    }

    public String upload(String fileName, String contentType, byte[] bytes) {
        String objectName = objectName(fileName);
        if (ossAvailable()) {
            ObjectMetadata metadata = new ObjectMetadata();
            metadata.setContentLength(bytes.length);
            if (StringUtils.hasText(contentType)) {
                metadata.setContentType(contentType);
            }
            try {
                ossClient.putObject(properties.getBucketName(), objectName, new ByteArrayInputStream(bytes), metadata);
                return ossUrl(objectName);
            } catch (RuntimeException ex) {
                log.warn("OSS upload failed, falling back to local file storage: {}", ex.getMessage());
            }
        }

        try {
            Path localFile = localPath(objectName);
            Files.createDirectories(localFile.getParent());
            Files.write(localFile, bytes);
            return localFile.toUri().toString();
        } catch (IOException ex) {
            throw new IllegalStateException("Local file storage failed", ex);
        }
    }

    private String objectName(String fileName) {
        String originalName = StringUtils.cleanPath(StringUtils.hasText(fileName) ? fileName : "file");
        String suffix = "";
        int dot = originalName.lastIndexOf('.');
        if (dot >= 0) {
            suffix = originalName.substring(dot);
        }
        return properties.getDirectory()
                + "/" + LocalDate.now()
                + "/" + UUID.randomUUID()
                + suffix;
    }

    private boolean ossAvailable() {
        return ossClient != null && StringUtils.hasText(properties.getBucketName());
    }

    private String ossUrl(String objectName) {
        if (StringUtils.hasText(properties.getUrlPrefix())) {
            return normalizeUrlPrefix(properties.getUrlPrefix()) + "/" + objectName;
        }
        return "https://" + properties.getBucketName() + "." + properties.getEndpoint().replaceFirst("^https?://", "") + "/" + objectName;
    }

    private Path localPath(String objectName) {
        Path baseDir = Path.of(properties.getLocalDirectory()).toAbsolutePath().normalize();
        Path resolved = baseDir.resolve(objectName.replace("/", File.separator)).normalize();
        if (!resolved.startsWith(baseDir)) {
            throw new IllegalArgumentException("Invalid local storage path");
        }
        return resolved;
    }

    private String normalizeUrlPrefix(String urlPrefix) {
        String normalized = urlPrefix.replaceAll("/$", "");
        if (normalized.startsWith("http://") || normalized.startsWith("https://")) {
            return normalized;
        }
        return "https://" + normalized;
    }
}
