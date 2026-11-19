package com.recruit_resume.service;

import com.aliyun.oss.OSS;
import com.recruit_resume.config.OssProperties;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.beans.factory.ObjectProvider;

import java.io.ByteArrayInputStream;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class OssStorageServiceTest {

    @TempDir
    Path tempDir;

    @Test
    void storesGeneratedPdfLocallyWhenOssClientUnavailable() throws Exception {
        @SuppressWarnings("unchecked")
        ObjectProvider<OSS> provider = mock(ObjectProvider.class);
        when(provider.getIfAvailable()).thenReturn(null);
        OssProperties properties = new OssProperties();
        properties.setLocalDirectory(tempDir.toString());
        OssStorageService service = new OssStorageService(provider, properties);
        byte[] bytes = "%PDF-1.4\nlocal fallback".getBytes();

        String url = service.upload("resume.pdf", "application/pdf", bytes);

        assertTrue(url.startsWith("file:///"));
        Path stored = Path.of(URI.create(url));
        assertTrue(stored.startsWith(tempDir));
        assertTrue(Files.exists(stored));
        assertArrayEquals(bytes, Files.readAllBytes(stored));
    }

    @Test
    void storesGeneratedPdfLocallyWhenOssUploadFails() throws Exception {
        OSS oss = mock(OSS.class);
        doThrow(new RuntimeException("UserDisable"))
                .when(oss).putObject(eq("disabled-bucket"), any(String.class), any(ByteArrayInputStream.class), any());
        @SuppressWarnings("unchecked")
        ObjectProvider<OSS> provider = mock(ObjectProvider.class);
        when(provider.getIfAvailable()).thenReturn(oss);
        OssProperties properties = new OssProperties();
        properties.setBucketName("disabled-bucket");
        properties.setLocalDirectory(tempDir.toString());
        OssStorageService service = new OssStorageService(provider, properties);
        byte[] bytes = "%PDF-1.4\nfallback after oss failure".getBytes();

        String url = service.upload("resume.pdf", "application/pdf", bytes);

        assertTrue(url.startsWith("file:///"));
        Path stored = Path.of(URI.create(url));
        assertTrue(stored.startsWith(tempDir));
        assertArrayEquals(bytes, Files.readAllBytes(stored));
    }
}
