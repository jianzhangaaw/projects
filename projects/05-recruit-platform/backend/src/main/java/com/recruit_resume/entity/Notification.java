package com.recruit_resume.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("notification")
public class Notification {

    @TableId
    private Long id;
    private Long receiverId;
    private String title;
    private String content;
    private String type;
    private Integer isRead;
    private LocalDateTime createdAt;
}
