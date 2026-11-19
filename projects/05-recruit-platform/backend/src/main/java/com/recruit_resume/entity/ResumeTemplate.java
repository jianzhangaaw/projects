package com.recruit_resume.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("resume_template")
public class ResumeTemplate {

    @TableId
    private Long id;
    private String templateName;
    private String templateCode;
    private Long coverFileId;
    @TableField(exist = false)
    private String coverUrl;
    private String description;
    private Integer enabled;
    private Integer sortOrder;
    private Integer version;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
