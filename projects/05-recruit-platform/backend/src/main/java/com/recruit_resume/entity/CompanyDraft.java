package com.recruit_resume.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("company_draft")
public class CompanyDraft {

    @TableId
    private Long id;
    private Long companyId;
    private String companyName;
    private String industry;
    private String companySize;
    private String contactName;
    private String contactPhone;
    private String description;
    private Long logoFileId;
    private String reviewStatus;
    private String reviewReason;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
