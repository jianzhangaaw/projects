package com.recruit_resume.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("student_experience")
public class StudentExperience {

    @TableId
    private Long id;
    private Long studentId;
    private String experienceType;
    private String title;
    private String timeRange;
    private String roleName;
    private String description;
    private Long fileId;
    @TableField(exist = false)
    private String fileUrl;
    private Integer sortOrder;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
