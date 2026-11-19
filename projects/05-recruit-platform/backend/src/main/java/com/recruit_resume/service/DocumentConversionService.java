package com.recruit_resume.service;

import com.recruit_resume.common.BusinessException;
import com.recruit_resume.config.FilePreviewProperties;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.concurrent.TimeUnit;

@Service
public class DocumentConversionService {

    private static final String WORD_PREVIEW_UNAVAILABLE = "Word 简历在线预览服务未配置或不可用，请联系管理员安装 LibreOffice";

    private final FilePreviewProperties properties;

    public DocumentConversionService(FilePreviewProperties properties) {
        this.properties = properties;
    }

    public Path convertWordToPdf(Path source, Path outputDir) throws IOException {
        Files.createDirectories(outputDir);
        runLibreOfficeConversion(source, outputDir);
        Path converted = outputDir.resolve(replaceExtension(source.getFileName().toString(), ".pdf"));
        if (!Files.exists(converted) || Files.size(converted) == 0) {
            throw new BusinessException("Word 简历转换 PDF 失败，请稍后重试");
        }
        return converted;
    }

    private void runLibreOfficeConversion(Path source, Path outputDir) throws IOException {
        Path userProfileDir = outputDir.resolve("lo-profile");
        Files.createDirectories(userProfileDir);
        Path outputLog = outputDir.resolve("soffice-output.log");
        ProcessBuilder builder = new ProcessBuilder(
                properties.getLibreOfficePath(),
                "-env:UserInstallation=" + userProfileDir.toUri(),
                "--headless",
                "--nologo",
                "--nofirststartwizard",
                "--norestore",
                "--convert-to",
                "pdf",
                "--outdir",
                outputDir.toString(),
                source.toString()
        );
        builder.redirectErrorStream(true);
        builder.redirectOutput(outputLog.toFile());
        Process process;
        try {
            process = builder.start();
        } catch (IOException ex) {
            throw new BusinessException(WORD_PREVIEW_UNAVAILABLE);
        }
        boolean finished;
        try {
            finished = process.waitFor(Duration.ofSeconds(properties.getConvertTimeoutSeconds()).toMillis(), TimeUnit.MILLISECONDS);
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            throw new BusinessException("Word 简历转换被中断，请稍后重试");
        }
        if (!finished) {
            process.destroyForcibly();
            throw new BusinessException("Word 简历转换超时，请稍后重试");
        }
        if (process.exitValue() != 0) {
            throw new BusinessException("Word 简历转换 PDF 失败，请稍后重试");
        }
    }

    private String replaceExtension(String fileName, String extension) {
        int dot = fileName.lastIndexOf('.');
        if (dot >= 0) {
            return fileName.substring(0, dot) + extension;
        }
        return fileName + extension;
    }
}
