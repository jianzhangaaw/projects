package com.recruit_resume.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class GenerateResumeRequest {

    private Long templateId;
    private ResumeGenerationSnapshot snapshot;
}
