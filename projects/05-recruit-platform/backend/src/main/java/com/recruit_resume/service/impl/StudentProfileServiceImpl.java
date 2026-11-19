package com.recruit_resume.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.recruit_resume.entity.StudentProfile;
import com.recruit_resume.mapper.StudentProfileMapper;
import com.recruit_resume.service.StudentProfileService;
import org.springframework.stereotype.Service;

@Service
public class StudentProfileServiceImpl extends ServiceImpl<StudentProfileMapper, StudentProfile> implements StudentProfileService {
}
