package com.recruit_resume.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("resume_snapshot")
public class ResumeSnapshot {

    @TableId
    private Long id;
    private Long resumeId;
    private Long studentId;
    private Long templateId;
    private String snapshotJson;
    private String htmlContent;
    private LocalDateTime generatedAt;
}
