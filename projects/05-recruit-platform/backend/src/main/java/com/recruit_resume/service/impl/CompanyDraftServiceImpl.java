package com.recruit_resume.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.recruit_resume.entity.CompanyDraft;
import com.recruit_resume.mapper.CompanyDraftMapper;
import com.recruit_resume.service.CompanyDraftService;
import org.springframework.stereotype.Service;

@Service
public class CompanyDraftServiceImpl extends ServiceImpl<CompanyDraftMapper, CompanyDraft> implements CompanyDraftService {
}
