package com.recruit_resume.controller;

import com.recruit_resume.common.BusinessException;
import com.recruit_resume.common.Result;
import com.recruit_resume.entity.ResumeTemplate;
import com.recruit_resume.security.CurrentUserContext;
import com.recruit_resume.service.ResumeTemplateService;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/admin/resume-templates")
public class AdminResumeTemplateController {

    private final ResumeTemplateService templateService;

    public AdminResumeTemplateController(ResumeTemplateService templateService) {
        this.templateService = templateService;
    }

    @GetMapping
    public Result<List<ResumeTemplate>> list() {
        CurrentUserContext.requireRole("ADMIN");
        return Result.success(templateService.listForAdmin());
    }

    @PostMapping
    public Result<ResumeTemplate> create(@RequestBody ResumeTemplate body) {
        CurrentUserContext.requireRole("ADMIN");
        validate(body);
        applyDefaults(body);
        templateService.save(body);
        return Result.success(templateService.withCoverUrl(body));
    }

    @PutMapping("/{id}")
    public Result<ResumeTemplate> update(@PathVariable Long id, @RequestBody ResumeTemplate body) {
        CurrentUserContext.requireRole("ADMIN");
        validate(body);
        body.setId(id);
        templateService.updateById(body);
        return Result.success(templateService.withCoverUrl(templateService.getById(id)));
    }

    @PatchMapping("/{id}/enabled")
    public Result<Void> updateEnabled(@PathVariable Long id, @RequestParam boolean enabled) {
        CurrentUserContext.requireRole("ADMIN");
        ResumeTemplate template = new ResumeTemplate();
        template.setId(id);
        template.setEnabled(enabled ? 1 : 0);
        templateService.updateById(template);
        return Result.success();
    }

    @PatchMapping("/{id}/sort")
    public Result<Void> updateSort(@PathVariable Long id, @RequestParam Integer sortOrder) {
        CurrentUserContext.requireRole("ADMIN");
        ResumeTemplate template = new ResumeTemplate();
        template.setId(id);
        template.setSortOrder(sortOrder == null ? 0 : sortOrder);
        templateService.updateById(template);
        return Result.success();
    }

    private void validate(ResumeTemplate template) {
        if (template == null || !StringUtils.hasText(template.getTemplateName())) {
            throw new BusinessException("Template name is required");
        }
        if (!StringUtils.hasText(template.getTemplateCode())) {
            throw new BusinessException("Template code is required");
        }
        if (!template.getTemplateCode().matches("[a-zA-Z0-9_-]+")) {
            throw new BusinessException("Template code can only contain letters, numbers, underscores and hyphens");
        }
    }

    private void applyDefaults(ResumeTemplate template) {
        if (template.getEnabled() == null) {
            template.setEnabled(1);
        }
        if (template.getSortOrder() == null) {
            template.setSortOrder(0);
        }
        if (template.getVersion() == null) {
            template.setVersion(1);
        }
    }
}
