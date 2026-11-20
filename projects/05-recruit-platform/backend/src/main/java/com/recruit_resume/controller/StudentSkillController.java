package com.recruit_resume.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.recruit_resume.common.Result;
import com.recruit_resume.entity.StudentSkill;
import com.recruit_resume.security.CurrentUser;
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
import java.util.Map;

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

    @Override
    protected boolean isOwnedBy(StudentSkill entity, CurrentUser user) {
        if (entity.getStudentId() == null) {
            return false;
        }
        return entity.getStudentId().equals(studentProfileResolver.getOrCreateCurrentStudentProfile().getId());
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
        // 批量装文件地址：原来是每条技能查一次 file_resource（N 条 = N 次查询）
        Map<Long, String> fileUrls = fileResourceService.fileUrlsByIds(
                skills.stream().map(StudentSkill::getFileId).toList());
        skills.forEach(skill -> {
            String url = skill.getFileId() == null ? null : fileUrls.get(skill.getFileId());
            if (url != null) {
                skill.setFileUrl(url);
            }
        });
        return Result.success(skills);
    }
}
