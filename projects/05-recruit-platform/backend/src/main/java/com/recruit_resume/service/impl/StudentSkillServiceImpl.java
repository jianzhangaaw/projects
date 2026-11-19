package com.recruit_resume.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.recruit_resume.entity.StudentSkill;
import com.recruit_resume.mapper.StudentSkillMapper;
import com.recruit_resume.service.StudentSkillService;
import org.springframework.stereotype.Service;

@Service
public class StudentSkillServiceImpl extends ServiceImpl<StudentSkillMapper, StudentSkill> implements StudentSkillService {
}
