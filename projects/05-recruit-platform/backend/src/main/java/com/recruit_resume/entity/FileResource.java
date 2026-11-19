package com.recruit_resume.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("file_resource")
public class FileResource {

    @TableId
    private Long id;
    private Long uploaderId;
    private String fileName;
    private String fileType;
    private String fileUrl;
    private Long fileSize;
    private String businessType;
    private LocalDateTime createdAt;
}
