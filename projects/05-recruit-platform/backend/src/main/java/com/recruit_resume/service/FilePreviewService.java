package com.recruit_resume.service;

import com.recruit_resume.common.BusinessException;
import com.recruit_resume.config.FilePreviewProperties;
import com.recruit_resume.entity.FileResource;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

@Service
public class FilePreviewService {

    private final FilePreviewProperties properties;
    private final DocumentConversionService documentConversionService;

    public FilePreviewService(FilePreviewProperties properties, DocumentConversionService documentConversionService) {
        this.properties = properties;
        this.documentConversionService = documentConversionService;
    }

    public void writePreview(FileResource resource, HttpServletResponse response) throws IOException {
        String fileName = StringUtils.hasText(resource.getFileName()) ? resource.getFileName() : "resume";
        if (isPdf(resource, fileName)) {
            writeRemoteFile(resource.getFileUrl(), response, "application/pdf", fileName);
            return;
        }
        if (isImage(resource, fileName)) {
            writeRemoteFile(resource.getFileUrl(), response, resolveImageContentType(resource, fileName), fileName);
            return;
        }
        if (isWord(fileName)) {
            Path pdf = convertWordToPdf(resource, fileName);
            writeLocalFile(pdf, response, "application/pdf", replaceExtension(fileName, ".pdf"));
            return;
        }
        throw new BusinessException("暂不支持该文件类型在线预览，请下载后查看");
    }

    private void writeRemoteFile(String url, HttpServletResponse response, String contentType, String fileName) throws IOException {
        if (!StringUtils.hasText(url)) {
            throw new BusinessException("文件地址不存在");
        }
        response.setContentType(contentType);
        response.setHeader(HttpHeaders.CONTENT_DISPOSITION, inlineDisposition(fileName));
        try (InputStream inputStream = URI.create(url).toURL().openStream()) {
            inputStream.transferTo(response.getOutputStream());
        }
    }

    private void writeLocalFile(Path file, HttpServletResponse response, String contentType, String fileName) throws IOException {
        response.setContentType(contentType);
        response.setHeader(HttpHeaders.CONTENT_DISPOSITION, inlineDisposition(fileName));
        response.setContentLengthLong(Files.size(file));
        Files.copy(file, response.getOutputStream());
    }

    private Path convertWordToPdf(FileResource resource, String fileName) throws IOException {
        Path cacheDir = Path.of(properties.getCacheDir());
        Files.createDirectories(cacheDir);
        Path cachedPdf = cacheDir.resolve(resource.getId() + ".pdf");
        if (Files.exists(cachedPdf) && Files.size(cachedPdf) > 0) {
            return cachedPdf;
        }

        Path workDir = Files.createTempDirectory(cacheDir, "word-preview-");
        Path source = workDir.resolve(fileName);
        try {
            downloadTo(resource.getFileUrl(), source);
            Path converted = documentConversionService.convertWordToPdf(source, workDir);
            Files.move(converted, cachedPdf, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
            return cachedPdf;
        } finally {
            deleteQuietly(workDir);
        }
    }

    private void downloadTo(String url, Path target) throws IOException {
        if (!StringUtils.hasText(url)) {
            throw new BusinessException("文件地址不存在");
        }
        try (InputStream inputStream = URI.create(url).toURL().openStream()) {
            Files.copy(inputStream, target, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        }
    }

    private boolean isPdf(FileResource resource, String fileName) {
        // resolveFileType 按扩展名存 "pdf"；兼容旧数据可能存 "application/pdf"
        String ft = resource.getFileType();
        String lowerName = fileName.toLowerCase(Locale.ROOT);
        return (ft != null && (ft.equalsIgnoreCase("pdf") || ft.equalsIgnoreCase("application/pdf")))
                || lowerName.endsWith(".pdf");
    }

    private boolean isImage(FileResource resource, String fileName) {
        String fileType = resource.getFileType();
        String lowerName = fileName.toLowerCase(Locale.ROOT);
        // fileType 既可能是 image/png（旧数据），也可能是 png（新版 resolveFileType）
        boolean isImageType = fileType != null
                && (fileType.toLowerCase(Locale.ROOT).startsWith("image/") || isImageExtension(fileType));
        return isImageType
                || lowerName.endsWith(".png")
                || lowerName.endsWith(".jpg")
                || lowerName.endsWith(".jpeg")
                || lowerName.endsWith(".gif")
                || lowerName.endsWith(".webp");
    }

    private boolean isImageExtension(String ext) {
        if (ext == null) return false;
        String lower = ext.toLowerCase(Locale.ROOT);
        return lower.equals("png") || lower.equals("jpg") || lower.equals("jpeg")
                || lower.equals("gif") || lower.equals("webp");
    }

    private boolean isWord(String fileName) {
        String lowerName = fileName.toLowerCase(Locale.ROOT);
        return lowerName.endsWith(".doc") || lowerName.endsWith(".docx");
    }

    private String resolveImageContentType(FileResource resource, String fileName) {
        String ft = resource.getFileType();
        // 旧数据存完整 MIME（如 image/png），新版 resolveFileType 存后缀（如 png）
        if (ft != null && ft.toLowerCase(Locale.ROOT).startsWith("image/")) {
            return ft;
        }
        if (ft != null && ft.equalsIgnoreCase("png")) {
            return "image/png";
        }
        if (ft != null && ft.equalsIgnoreCase("gif")) {
            return "image/gif";
        }
        if (ft != null && ft.equalsIgnoreCase("webp")) {
            return "image/webp";
        }
        String lowerName = fileName.toLowerCase(Locale.ROOT);
        if (lowerName.endsWith(".png")) {
            return "image/png";
        }
        if (lowerName.endsWith(".gif")) {
            return "image/gif";
        }
        if (lowerName.endsWith(".webp")) {
            return "image/webp";
        }
        return "image/jpeg";
    }

    private String inlineDisposition(String fileName) {
        String encoded = URLEncoder.encode(fileName, StandardCharsets.UTF_8).replace("+", "%20");
        return "inline; filename*=UTF-8''" + encoded;
    }

    private String replaceExtension(String fileName, String extension) {
        int dot = fileName.lastIndexOf('.');
        if (dot >= 0) {
            return fileName.substring(0, dot) + extension;
        }
        return fileName + extension;
    }

    private void deleteQuietly(Path path) {
        if (!Files.exists(path)) {
            return;
        }
        try (var stream = Files.walk(path)) {
            stream.sorted((a, b) -> b.compareTo(a)).forEach(item -> {
                try {
                    Files.deleteIfExists(item);
                } catch (IOException ignored) {
                    // Best effort cleanup for temporary conversion files.
                }
            });
        } catch (IOException ignored) {
            // Best effort cleanup for temporary conversion files.
        }
    }
}
