package com.recruit_resume.dto;

import com.recruit_resume.entity.ResumeTemplate;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class ResumeGenerationContextResponse {

    private List<ResumeTemplate> templates;
    private Long defaultTemplateId;
    private ResumeGenerationSnapshot snapshot;
}
