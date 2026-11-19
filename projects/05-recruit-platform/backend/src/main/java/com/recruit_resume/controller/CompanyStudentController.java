package com.recruit_resume.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.recruit_resume.common.BusinessException;
import com.recruit_resume.common.Result;
import com.recruit_resume.common.ResultCode;
import com.recruit_resume.dto.StudentDetailResponse;
import com.recruit_resume.entity.Company;
import com.recruit_resume.entity.JobApplication;
import com.recruit_resume.entity.StudentExperience;
import com.recruit_resume.entity.StudentProfile;
import com.recruit_resume.entity.StudentSkill;
import com.recruit_resume.security.CurrentUserContext;
import com.recruit_resume.service.CompanyService;
import com.recruit_resume.service.JobApplicationService;
import com.recruit_resume.service.StudentExperienceService;
import com.recruit_resume.service.StudentProfileService;
import com.recruit_resume.service.StudentSkillService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/company")
public class CompanyStudentController {

    private final StudentProfileService studentProfileService;
    private final StudentSkillService studentSkillService;
    private final StudentExperienceService studentExperienceService;
    private final JobApplicationService jobApplicationService;
    private final CompanyService companyService;

    public CompanyStudentController(
            StudentProfileService studentProfileService,
            StudentSkillService studentSkillService,
            StudentExperienceService studentExperienceService,
            JobApplicationService jobApplicationService,
            CompanyService companyService
    ) {
        this.studentProfileService = studentProfileService;
        this.studentSkillService = studentSkillService;
        this.studentExperienceService = studentExperienceService;
        this.jobApplicationService = jobApplicationService;
        this.companyService = companyService;
    }

    @GetMapping("/student-detail/{studentId}")
    public Result<StudentDetailResponse> getStudentDetail(@PathVariable Long studentId) {
        Long companyId = getCurrentCompanyId();

        boolean hasApplied = jobApplicationService.count(new LambdaQueryWrapper<JobApplication>()
                .eq(JobApplication::getStudentId, studentId)
                .eq(JobApplication::getCompanyId, companyId)) > 0;

        if (!hasApplied) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }

        StudentProfile profile = studentProfileService.getById(studentId);
        if (profile == null) {
            throw new BusinessException("学生资料不存在");
        }

        List<StudentSkill> skills = studentSkillService.list(new LambdaQueryWrapper<StudentSkill>()
                .eq(StudentSkill::getStudentId, studentId));

        List<StudentExperience> experiences = studentExperienceService.list(new LambdaQueryWrapper<StudentExperience>()
                .eq(StudentExperience::getStudentId, studentId)
                .orderByAsc(StudentExperience::getSortOrder));

        StudentDetailResponse response = new StudentDetailResponse();
        response.setProfile(profile);
        response.setSkills(skills);
        response.setExperiences(experiences);
        return Result.success(response);
    }

    private Long getCurrentCompanyId() {
        Company company = companyService.getOne(new LambdaQueryWrapper<Company>()
                .eq(Company::getUserId, CurrentUserContext.userId())
                .last("limit 1"));
        if (company == null) {
            throw new BusinessException("请先完善企业信息");
        }
        return company.getId();
    }
}
