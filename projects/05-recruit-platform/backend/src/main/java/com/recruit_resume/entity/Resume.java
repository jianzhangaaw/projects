package com.recruit_resume.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@TableName("resume")
public class Resume {

    @TableId
    private Long id;
    private Long studentId;
    private String resumeName;
    private String resumeType;

    @NotBlank(message = "目标岗位不能为空")
    private String targetPosition;

    private Long fileId;

    @TableField(exist = false)
    private String fileUrl;

    @NotBlank(message = "学校不能为空")
    private String school;

    @NotBlank(message = "专业不能为空")
    private String major;

    private String educationLevel;
    private LocalDate graduationDate;
    private String skillTags;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
