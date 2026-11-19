package com.recruit_resume.service;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.recruit_resume.dto.ResumeGenerationSnapshot;
import com.recruit_resume.entity.StudentExperience;
import com.recruit_resume.entity.StudentProfile;
import com.recruit_resume.entity.StudentSkill;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class ResumeDataAssemblerTest {

    @Test
    void buildsSnapshotFromCurrentStudentDataWithoutSavingProfileChanges() {
        StudentProfileResolver profileResolver = mock(StudentProfileResolver.class);
        StudentSkillService skillService = mock(StudentSkillService.class);
        StudentExperienceService experienceService = mock(StudentExperienceService.class);
        StudentProfile profile = new StudentProfile();
        profile.setId(20L);
        profile.setRealName("Zhang San");
        profile.setExpectedPosition("Java Backend");
        profile.setSchool("BUPT");
        profile.setMajor("Software Engineering");
        profile.setEducationLevel("Bachelor");
        profile.setGraduationDate(LocalDate.of(2026, 7, 1));
        StudentSkill skill = new StudentSkill();
        skill.setSkillName("Java");
        StudentExperience experience = new StudentExperience();
        experience.setTitle("Campus Recruiting Platform");
        when(profileResolver.getOrCreateCurrentStudentProfile()).thenReturn(profile);
        when(skillService.list(any(Wrapper.class))).thenReturn(List.of(skill));
        when(experienceService.list(any(Wrapper.class))).thenReturn(List.of(experience));
        ResumeDataAssembler assembler = new ResumeDataAssembler(
                profileResolver,
                skillService,
                experienceService
        );

        ResumeGenerationSnapshot snapshot = assembler.buildSnapshotForCurrentStudent();

        assertEquals("Zhang San-Java Backend-Generated Resume", snapshot.getResumeName());
        assertEquals("Java Backend", snapshot.getTargetPosition());
        assertEquals("BUPT", snapshot.getProfile().getSchool());
        assertEquals("Java", snapshot.getSkills().get(0).getSkillName());
        assertEquals("Campus Recruiting Platform", snapshot.getExperiences().get(0).getTitle());
    }
}
