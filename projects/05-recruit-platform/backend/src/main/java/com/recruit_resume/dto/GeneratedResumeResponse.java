package com.recruit_resume.dto;

import com.recruit_resume.entity.Resume;
import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class GeneratedResumeResponse {

    private Resume resume;
    private Long pdfFileId;
    private String pdfFileUrl;
    private Long snapshotId;
    private Long templateId;
}
