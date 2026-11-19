package com.recruit_resume.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.recruit_resume.common.BusinessException;
import com.recruit_resume.common.Result;
import com.recruit_resume.common.ResultCode;
import com.recruit_resume.dto.GenerateResumeRequest;
import com.recruit_resume.dto.GeneratedResumeResponse;
import com.recruit_resume.dto.ResumeGenerationContextResponse;
import com.recruit_resume.entity.FileResource;
import com.recruit_resume.entity.Resume;
import com.recruit_resume.entity.ResumeSnapshot;
import com.recruit_resume.entity.ResumeTemplate;
import com.recruit_resume.security.CurrentUser;
import com.recruit_resume.security.CurrentUserContext;
import com.recruit_resume.service.FileResourceService;
import com.recruit_resume.service.ResumeGenerationService;
import com.recruit_resume.service.ResumeSnapshotService;
import com.recruit_resume.service.ResumeService;
import com.recruit_resume.service.ResumeTemplateService;
import com.recruit_resume.service.StudentProfileResolver;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import jakarta.validation.Valid;
import java.util.List;

@RestController
@RequestMapping("/api/student/resumes")
public class ResumeController extends BaseCrudController<Resume> {

    private final ResumeService service;
    private final FileResourceService fileResourceService;
    private final StudentProfileResolver studentProfileResolver;
    private final ResumeGenerationService resumeGenerationService;
    private final ResumeTemplateService resumeTemplateService;
    private final ResumeSnapshotService resumeSnapshotService;

    public ResumeController(
            ResumeService service,
            FileResourceService fileResourceService,
            StudentProfileResolver studentProfileResolver,
            ResumeGenerationService resumeGenerationService,
            ResumeTemplateService resumeTemplateService,
            ResumeSnapshotService resumeSnapshotService
    ) {
        super(service);
        this.service = service;
        this.fileResourceService = fileResourceService;
        this.studentProfileResolver = studentProfileResolver;
        this.resumeGenerationService = resumeGenerationService;
        this.resumeTemplateService = resumeTemplateService;
        this.resumeSnapshotService = resumeSnapshotService;
    }

    @Override
    protected boolean isOwnedBy(Resume entity, CurrentUser user) {
        if (entity.getStudentId() == null) {
            return false;
        }
        return entity.getStudentId().equals(studentProfileResolver.getOrCreateCurrentStudentProfile().getId());
    }

    @PostMapping
    public Result<Resume> create(@Valid @RequestBody Resume body) {
        body.setStudentId(studentProfileResolver.getOrCreateCurrentStudentProfile().getId());
        service.save(body);
        return Result.success(body);
    }

    @PutMapping("/{id}")
    public Result<Resume> update(@PathVariable Long id, @Valid @RequestBody Resume body) {
        Resume existing = service.getById(id);
        if (existing == null) {
            throw new BusinessException(ResultCode.NOT_FOUND);
        }
        Long profileId = studentProfileResolver.getOrCreateCurrentStudentProfile().getId();
        if (!profileId.equals(existing.getStudentId())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        body.setId(id);
        body.setStudentId(profileId);
        service.updateById(body);
        return Result.success(body);
    }

    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        Resume resume = service.getById(id);
        if (resume == null) {
            throw new BusinessException(ResultCode.NOT_FOUND);
        }
        Long profileId = studentProfileResolver.getOrCreateCurrentStudentProfile().getId();
        if (!profileId.equals(resume.getStudentId())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        service.removeById(id);
        return Result.success();
    }

    @GetMapping("/templates")
    public Result<List<ResumeTemplate>> templates() {
        return Result.success(resumeTemplateService.listActiveTemplates());
    }

    @GetMapping("/generation-context")
    public Result<ResumeGenerationContextResponse> generationContext() {
        if (!"STUDENT".equals(CurrentUserContext.role())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        return Result.success(resumeGenerationService.buildContextForCurrentStudent());
    }

    @PostMapping("/generate")
    public Result<GeneratedResumeResponse> generate(@RequestBody(required = false) GenerateResumeRequest request) {
        if (!"STUDENT".equals(CurrentUserContext.role())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        if (request == null) {
            return Result.success(resumeGenerationService.generateForCurrentStudent());
        }
        return Result.success(resumeGenerationService.generateForCurrentStudent(request));
    }

    @GetMapping("/{id}/snapshot")
    public Result<ResumeSnapshot> snapshot(@PathVariable Long id) {
        return Result.success(resumeSnapshotService.getByResumeIdForCurrentStudent(id));
    }

    @GetMapping("/by-student")
    public Result<List<Resume>> listByStudent(@RequestParam Long studentId) {
        if (!CurrentUserContext.isAdmin()) {
            studentId = studentProfileResolver.getOrCreateCurrentStudentProfile().getId();
        }
        List<Resume> resumes = service.list(new LambdaQueryWrapper<Resume>()
                .eq(Resume::getStudentId, studentId));
        resumes.forEach(resume -> {
            if (resume.getFileId() != null) {
                FileResource file = fileResourceService.getById(resume.getFileId());
                if (file != null) {
                    resume.setFileUrl(file.getFileUrl());
                }
            }
        });
        return Result.success(resumes);
    }
}
