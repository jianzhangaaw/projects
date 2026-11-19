package com.recruit_resume.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.recruit_resume.common.Result;
import com.recruit_resume.entity.FileResource;
import com.recruit_resume.entity.StudentExperience;
import com.recruit_resume.security.CurrentUser;
import com.recruit_resume.security.CurrentUserContext;
import com.recruit_resume.service.FileResourceService;
import com.recruit_resume.service.StudentProfileResolver;
import com.recruit_resume.service.StudentExperienceService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/student/experiences")
public class StudentExperienceController extends BaseCrudController<StudentExperience> {

    private final StudentExperienceService service;
    private final FileResourceService fileResourceService;
    private final StudentProfileResolver studentProfileResolver;

    public StudentExperienceController(
            StudentExperienceService service,
            FileResourceService fileResourceService,
            StudentProfileResolver studentProfileResolver
    ) {
        super(service);
        this.service = service;
        this.fileResourceService = fileResourceService;
        this.studentProfileResolver = studentProfileResolver;
    }

    @Override
    protected boolean isOwnedBy(StudentExperience entity, CurrentUser user) {
        if (entity.getStudentId() == null) {
            return false;
        }
        return entity.getStudentId().equals(studentProfileResolver.getOrCreateCurrentStudentProfile().getId());
    }

    @PostMapping
    public Result<StudentExperience> create(@RequestBody StudentExperience body) {
        body.setStudentId(studentProfileResolver.getOrCreateCurrentStudentProfile().getId());
        service.save(body);
        return Result.success(body);
    }

    @GetMapping("/by-student")
    public Result<List<StudentExperience>> listByStudent(@RequestParam Long studentId) {
        if (!CurrentUserContext.isAdmin()) {
            studentId = studentProfileResolver.getOrCreateCurrentStudentProfile().getId();
        }
        List<StudentExperience> experiences = service.list(new LambdaQueryWrapper<StudentExperience>()
                .eq(StudentExperience::getStudentId, studentId)
                .orderByAsc(StudentExperience::getSortOrder));
        experiences.forEach(experience -> {
            if (experience.getFileId() != null) {
                FileResource file = fileResourceService.getById(experience.getFileId());
                if (file != null) {
                    experience.setFileUrl(file.getFileUrl());
                }
            }
        });
        return Result.success(experiences);
    }
}
