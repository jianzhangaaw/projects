package com.recruit_resume.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("job")
public class Job {

    @TableId
    private Long id;
    private Long companyId;
    private String jobName;
    private String jobType;
    private String city;
    private String salaryRange;
    private String educationRequirement;
    private String majorRequirement;
    private String skillRequirement;
    private String description;
    private String status;
    private String reviewReason;
    private Integer viewCount;
    @TableField(exist = false)
    private String companyName;
    @TableField(exist = false)
    private String industry;
    @TableField(exist = false)
    private String companySize;
    @TableField(exist = false)
    private Long logoFileId;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
