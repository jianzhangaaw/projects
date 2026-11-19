package com.recruit_resume.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.recruit_resume.entity.Resume;
import com.recruit_resume.mapper.ResumeMapper;
import com.recruit_resume.service.ResumeService;
import org.springframework.stereotype.Service;

@Service
public class ResumeServiceImpl extends ServiceImpl<ResumeMapper, Resume> implements ResumeService {
}
