package com.recruit_resume.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("user_account")
public class UserAccount {

    @TableId
    private Long id;
    private String username;
    private String password;
    private String email;
    private String phone;
    private String role;
    private String status;

    @TableField(exist = false)
    private String associatedName;

    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
