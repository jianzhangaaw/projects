package com.recruit_resume.dto;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class StudentApplicationDetail {
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
    private String companyName;
    private String resumeName;
    private String resumeType;
    private String targetPosition;
    private Long resumeFileId;
}
