package com.recruit_resume.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class FileUploadResponse {

    private Long id;
    private String fileName;
    private String fileUrl;
}
