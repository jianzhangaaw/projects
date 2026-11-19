package com.recruit_resume.controller;

import com.recruit_resume.common.BusinessException;
import com.recruit_resume.common.Result;
import com.recruit_resume.common.ResultCode;
import com.recruit_resume.dto.FileUploadResponse;
import com.recruit_resume.entity.FileResource;
import com.recruit_resume.security.CurrentUserContext;
import com.recruit_resume.service.FilePreviewService;
import com.recruit_resume.service.FileResourceService;
import com.recruit_resume.service.OssStorageService;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.Locale;
import java.util.Set;

@Slf4j
@RestController
@RequestMapping("/api/files")
public class FileResourceController {

    private static final Set<String> BUSINESS_TYPES = Set.of("RESUME", "AVATAR", "LOGO", "CERTIFICATE", "TEMPLATE_COVER");

    private final FileResourceService fileResourceService;
    private final OssStorageService ossStorageService;
    private final FilePreviewService filePreviewService;

    public FileResourceController(
            FileResourceService fileResourceService,
            OssStorageService ossStorageService,
            FilePreviewService filePreviewService
    ) {
        this.fileResourceService = fileResourceService;
        this.ossStorageService = ossStorageService;
        this.filePreviewService = filePreviewService;
    }

    @PostMapping("/upload")
    public Result<FileUploadResponse> upload(
            @RequestParam(required = false) String businessType,
            @RequestParam(required = false) String bizType,
            @RequestParam MultipartFile file
    ) throws IOException {
        String resolvedBusinessType = StringUtils.hasText(businessType) ? businessType : bizType;
        validateUpload(file, resolvedBusinessType);

        String url = ossStorageService.upload(file);
        FileResource resource = new FileResource();
        resource.setUploaderId(CurrentUserContext.userId());
        resource.setBusinessType(resolvedBusinessType);
        resource.setFileName(file.getOriginalFilename());
        resource.setFileType(resolveFileType(file));
        resource.setFileSize(file.getSize());
        resource.setFileUrl(url);
        fileResourceService.save(resource);
        log.info("文件上传成功: id={}, fileName={}, size={} bytes, type={}, uploaderId={}",
                resource.getId(), resource.getFileName(), resource.getFileSize(),
                resolvedBusinessType, CurrentUserContext.userId());
        return Result.success(new FileUploadResponse(resource.getId(), resource.getFileName(), resource.getFileUrl()));
    }

    @GetMapping("/{id}")
    public Result<FileResource> get(@PathVariable Long id) {
        FileResource resource = getAccessibleFile(id);
        return Result.success(resource);
    }

    @GetMapping("/{id}/preview")
    public void preview(@PathVariable Long id, HttpServletResponse response) throws IOException {
        FileResource resource = getAccessibleFile(id);
        filePreviewService.writePreview(resource, response);
    }

    @GetMapping("/{id}/download")
    public void download(@PathVariable Long id, HttpServletResponse response) throws IOException {
        redirectToFile(id, response);
    }

    private void validateUpload(MultipartFile file, String businessType) {
        if (file == null || file.isEmpty()) {
            throw new BusinessException("上传文件不能为空");
        }
        if (!StringUtils.hasText(businessType) || !BUSINESS_TYPES.contains(businessType)) {
            throw new BusinessException("文件业务类型只能是 RESUME、AVATAR、LOGO、CERTIFICATE、TEMPLATE_COVER");
        }
    }

    private String resolveFileType(MultipartFile file) {
        String originalFilename = file.getOriginalFilename();
        if (StringUtils.hasText(originalFilename)) {
            int dot = originalFilename.lastIndexOf('.');
            if (dot >= 0 && dot < originalFilename.length() - 1) {
                return originalFilename.substring(dot + 1).toLowerCase(Locale.ROOT);
            }
        }
        String contentType = file.getContentType();
        if (!StringUtils.hasText(contentType)) {
            return "unknown";
        }
        int slash = contentType.lastIndexOf('/');
        String value = slash >= 0 ? contentType.substring(slash + 1) : contentType;
        return value.length() > 50 ? value.substring(0, 50) : value;
    }

    private FileResource getAccessibleFile(Long id) {
        FileResource resource = fileResourceService.getById(id);
        if (resource == null) {
            throw new BusinessException(ResultCode.NOT_FOUND);
        }
        // 管理员和上传者始终有权限，企业用户可查看简历文件
        if (CurrentUserContext.isAdmin() || CurrentUserContext.userId().equals(resource.getUploaderId())) {
            return resource;
        }
        if ("COMPANY".equals(CurrentUserContext.role()) && "RESUME".equals(resource.getBusinessType())) {
            return resource;
        }
        throw new BusinessException(ResultCode.FORBIDDEN);
    }

    private void redirectToFile(Long id, HttpServletResponse response) throws IOException {
        FileResource resource = getAccessibleFile(id);
        if (!StringUtils.hasText(resource.getFileUrl())) {
            throw new BusinessException("文件地址不存在");
        }
        response.sendRedirect(resource.getFileUrl());
    }
}
