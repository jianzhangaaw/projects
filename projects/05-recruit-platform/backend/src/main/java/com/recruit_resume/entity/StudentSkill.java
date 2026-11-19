package com.recruit_resume.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("student_skill")
public class StudentSkill {

    @TableId
    private Long id;
    private Long studentId;
    private String skillName;
    private String skillType;
    private String proficiency;
    private BigDecimal years;
    private Long fileId;
    @TableField(exist = false)
    private String fileUrl;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
