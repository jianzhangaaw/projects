package com.recruit_resume.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.recruit_resume.common.Result;
import com.recruit_resume.entity.FileResource;
import com.recruit_resume.entity.StudentSkill;
import com.recruit_resume.security.CurrentUserContext;
import com.recruit_resume.service.FileResourceService;
import com.recruit_resume.service.StudentProfileResolver;
import com.recruit_resume.service.StudentSkillService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/student/skills")
public class StudentSkillController extends BaseCrudController<StudentSkill> {

    private final StudentSkillService service;
    private final FileResourceService fileResourceService;
    private final StudentProfileResolver studentProfileResolver;

    public StudentSkillController(
            StudentSkillService service,
            FileResourceService fileResourceService,
            StudentProfileResolver studentProfileResolver
    ) {
        super(service);
        this.service = service;
        this.fileResourceService = fileResourceService;
        this.studentProfileResolver = studentProfileResolver;
    }

    @PostMapping
    public Result<StudentSkill> create(@RequestBody StudentSkill body) {
        body.setStudentId(studentProfileResolver.getOrCreateCurrentStudentProfile().getId());
        service.save(body);
        return Result.success(body);
    }

    @GetMapping("/by-student")
    public Result<List<StudentSkill>> listByStudent(@RequestParam Long studentId) {
        if (!CurrentUserContext.isAdmin()) {
            studentId = studentProfileResolver.getOrCreateCurrentStudentProfile().getId();
        }
        List<StudentSkill> skills = service.list(new LambdaQueryWrapper<StudentSkill>()
                .eq(StudentSkill::getStudentId, studentId));
        skills.forEach(skill -> {
            if (skill.getFileId() != null) {
                FileResource file = fileResourceService.getById(skill.getFileId());
                if (file != null) {
                    skill.setFileUrl(file.getFileUrl());
                }
            }
        });
        return Result.success(skills);
    }
}
