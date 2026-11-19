package com.recruit_resume.service;

import com.recruit_resume.common.BusinessException;
import com.recruit_resume.config.FilePreviewProperties;
import com.recruit_resume.entity.FileResource;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.mock.web.MockHttpServletResponse;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class FilePreviewServiceTest {

    @TempDir
    Path tempDir;

    @Test
    void writesPdfPreviewInline() throws Exception {
        byte[] pdfBytes = "%PDF-1.4\nfake resume".getBytes();
        Path pdf = tempDir.resolve("resume.pdf");
        Files.write(pdf, pdfBytes);
        FileResource resource = fileResource("resume.pdf", "application/pdf", pdf);
        FilePreviewProperties properties = properties("missing-soffice");
        FilePreviewService service = new FilePreviewService(properties, new DocumentConversionService(properties));
        MockHttpServletResponse response = new MockHttpServletResponse();

        service.writePreview(resource, response);

        assertEquals("application/pdf", response.getContentType());
        assertTrue(response.getHeader("Content-Disposition").startsWith("inline;"));
        assertArrayEquals(pdfBytes, response.getContentAsByteArray());
    }

    @Test
    void wordPreviewReportsLibreOfficeConfigurationError() throws Exception {
        Path docx = tempDir.resolve("resume.docx");
        Files.writeString(docx, "fake word file");
        FileResource resource = fileResource(
                "resume.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                docx
        );
        FilePreviewProperties properties = properties("missing-soffice");
        FilePreviewService service = new FilePreviewService(properties, new DocumentConversionService(properties));
        MockHttpServletResponse response = new MockHttpServletResponse();

        BusinessException exception = assertThrows(
                BusinessException.class,
                () -> service.writePreview(resource, response)
        );

        assertEquals("Word 简历在线预览服务未配置或不可用，请联系管理员安装 LibreOffice", exception.getMessage());
    }

    @Test
    void wordPreviewUsesIsolatedLibreOfficeProfile() throws Exception {
        Path docx = tempDir.resolve("resume.docx");
        Files.writeString(docx, "fake word file");
        Path argLog = tempDir.resolve("soffice-args.txt");
        Path fakeSoffice = tempDir.resolve("fake-soffice.cmd");
        Path cacheDir = tempDir.resolve("preview-cache");
        Files.writeString(fakeSoffice, """
                @echo off
                echo %* > "__ARG_LOG__"
                for /d %%D in ("__CACHE_DIR__\\word-preview-*") do echo fake pdf > "%%D\\resume.pdf"
                exit /b 0
                """.replace("__ARG_LOG__", argLog.toString())
                .replace("__CACHE_DIR__", cacheDir.toString()));
        FileResource resource = fileResource("resume.docx", "docx", docx);
        FilePreviewProperties properties = properties(fakeSoffice.toString());
        FilePreviewService service = new FilePreviewService(properties, new DocumentConversionService(properties));
        MockHttpServletResponse response = new MockHttpServletResponse();

        service.writePreview(resource, response);

        assertEquals("application/pdf", response.getContentType());
        assertTrue(Files.readString(argLog).contains("-env:UserInstallation=file:///"));
    }

    private FilePreviewProperties properties(String libreOfficePath) {
        FilePreviewProperties properties = new FilePreviewProperties();
        properties.setLibreOfficePath(libreOfficePath);
        properties.setCacheDir(tempDir.resolve("preview-cache").toString());
        properties.setConvertTimeoutSeconds(1);
        return properties;
    }

    private FileResource fileResource(String fileName, String fileType, Path path) {
        FileResource resource = new FileResource();
        resource.setId(7L);
        resource.setFileName(fileName);
        resource.setFileType(fileType);
        resource.setFileUrl(path.toUri().toString());
        resource.setBusinessType("RESUME");
        return resource;
    }
}
