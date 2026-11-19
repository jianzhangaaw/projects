package com.recruit_resume.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.recruit_resume.dto.ResumeGenerationSnapshot;
import com.recruit_resume.entity.StudentExperience;
import com.recruit_resume.entity.StudentProfile;
import com.recruit_resume.entity.StudentSkill;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.List;

@Service
public class ResumeDataAssembler {

    private final StudentProfileResolver studentProfileResolver;
    private final StudentSkillService skillService;
    private final StudentExperienceService experienceService;

    public ResumeDataAssembler(
            StudentProfileResolver studentProfileResolver,
            StudentSkillService skillService,
            StudentExperienceService experienceService
    ) {
        this.studentProfileResolver = studentProfileResolver;
        this.skillService = skillService;
        this.experienceService = experienceService;
    }

    public ResumeGenerationSnapshot buildSnapshotForCurrentStudent() {
        StudentProfile profile = studentProfileResolver.getOrCreateCurrentStudentProfile();
        List<StudentSkill> skills = skillService.list(new LambdaQueryWrapper<StudentSkill>()
                .eq(StudentSkill::getStudentId, profile.getId()));
        List<StudentExperience> experiences = experienceService.list(new LambdaQueryWrapper<StudentExperience>()
                .eq(StudentExperience::getStudentId, profile.getId())
                .orderByAsc(StudentExperience::getSortOrder));
        return new ResumeGenerationSnapshot(
                buildResumeName(profile),
                profile.getExpectedPosition(),
                profile,
                skills,
                experiences
        );
    }

    public Long currentStudentId() {
        return studentProfileResolver.getOrCreateCurrentStudentProfile().getId();
    }

    private String buildResumeName(StudentProfile profile) {
        String name = StringUtils.hasText(profile.getRealName()) ? profile.getRealName() : "Student";
        String position = StringUtils.hasText(profile.getExpectedPosition()) ? profile.getExpectedPosition() : "Job";
        return name + "-" + position + "-Generated Resume";
    }
}
