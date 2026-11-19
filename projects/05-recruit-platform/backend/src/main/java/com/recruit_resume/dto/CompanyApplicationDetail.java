package com.recruit_resume.dto;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class CompanyApplicationDetail {

    private Long id;
    private Long jobId;
    private Long companyId;
    private Long studentId;
    private Long resumeId;
    private String status;
    private String remark;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    private String jobName;
    private String jobType;
    private String city;
    private String salaryRange;

    private String studentName;
    private String school;
    private String major;
    private String educationLevel;

    private String resumeName;
    private String resumeType;
    private String targetPosition;
    private Long resumeFileId;

    private String phone;
    private String email;
    private String gender;
}
