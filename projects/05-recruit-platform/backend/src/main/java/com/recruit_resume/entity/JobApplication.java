package com.recruit_resume.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("job_application")
public class JobApplication {

    @TableId
    private Long id;
    private Long jobId;
    private Long companyId;
    private Long studentId;
    private Long resumeId;
    private String status;
    private String remark;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
