package com.recruit_resume.dto;

import com.recruit_resume.entity.StudentExperience;
import com.recruit_resume.entity.StudentProfile;
import com.recruit_resume.entity.StudentSkill;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ResumeGenerationSnapshot {

    private String resumeName;
    private String targetPosition;
    private StudentProfile profile;
    private List<StudentSkill> skills = new ArrayList<>();
    private List<StudentExperience> experiences = new ArrayList<>();
}
