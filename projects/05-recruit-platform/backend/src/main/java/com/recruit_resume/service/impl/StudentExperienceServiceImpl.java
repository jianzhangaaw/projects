package com.recruit_resume.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.recruit_resume.entity.StudentExperience;
import com.recruit_resume.mapper.StudentExperienceMapper;
import com.recruit_resume.service.StudentExperienceService;
import org.springframework.stereotype.Service;

@Service
public class StudentExperienceServiceImpl extends ServiceImpl<StudentExperienceMapper, StudentExperience> implements StudentExperienceService {
}
