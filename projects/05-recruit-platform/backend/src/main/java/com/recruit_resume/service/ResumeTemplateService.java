package com.recruit_resume.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.recruit_resume.entity.ResumeTemplate;

import java.util.List;

public interface ResumeTemplateService extends IService<ResumeTemplate> {

    List<ResumeTemplate> listActiveTemplates();

    ResumeTemplate requireActiveTemplate(Long templateId);

    List<ResumeTemplate> listForAdmin();

    ResumeTemplate withCoverUrl(ResumeTemplate template);
}
