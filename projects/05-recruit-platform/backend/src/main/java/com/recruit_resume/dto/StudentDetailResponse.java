package com.recruit_resume.dto;

import com.recruit_resume.entity.StudentExperience;
import com.recruit_resume.entity.StudentProfile;
import com.recruit_resume.entity.StudentSkill;
import lombok.Data;

import java.util.List;

@Data
public class StudentDetailResponse {

    private StudentProfile profile;
    private List<StudentSkill> skills;
    private List<StudentExperience> experiences;
}
