package com.recruit_resume;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@MapperScan("com.recruit_resume.mapper")
@SpringBootApplication
public class RecruitResumeApplication {

    public static void main(String[] args) {
        SpringApplication.run(RecruitResumeApplication.class, args);
    }

}
