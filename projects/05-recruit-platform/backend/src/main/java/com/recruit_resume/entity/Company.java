package com.recruit_resume.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("company")
public class Company {

    @TableId
    private Long id;
    private Long userId;
    private String companyName;
    private String industry;
    private String companySize;
    private String contactName;
    private String contactPhone;
    private String description;
    private Long logoFileId;
    private String reviewStatus;
    private String reviewReason;

    @TableField(exist = false)
    private String reviewType;

    @TableField(exist = false)
    private String oldCompanyName;
    @TableField(exist = false)
    private String oldIndustry;
    @TableField(exist = false)
    private String oldCompanySize;
    @TableField(exist = false)
    private String oldContactName;
    @TableField(exist = false)
    private String oldContactPhone;
    @TableField(exist = false)
    private String oldDescription;

    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
