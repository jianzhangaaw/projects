package com.recruit_resume.entity;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@TableName("student_profile")
public class StudentProfile {

    @TableId
    private Long id;
    private Long userId;

    @NotBlank(message = "姓名不能为空")
    private String realName;

    private String gender;
    private Integer age;
    private String hometown;
    private String politicalStatus;

    @NotBlank(message = "手机号不能为空")
    @Pattern(regexp = "^1[3-9]\\d{9}$", message = "手机号格式不正确")
    private String phone;

    @NotBlank(message = "邮箱不能为空")
    private String email;

    private String wechat;
    private String qq;
    private String school;
    private String major;
    private String educationLevel;
    private String gpa;
    private LocalDate graduationDate;
    private String expectedPosition;
    private String expectedCity;
    private String expectedSalary;
    private String selfIntro;
    private Long avatarFileId;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
