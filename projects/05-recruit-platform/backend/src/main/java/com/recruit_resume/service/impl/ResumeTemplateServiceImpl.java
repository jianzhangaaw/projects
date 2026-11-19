package com.recruit_resume.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.recruit_resume.common.BusinessException;
import com.recruit_resume.common.ResultCode;
import com.recruit_resume.entity.FileResource;
import com.recruit_resume.entity.ResumeTemplate;
import com.recruit_resume.mapper.ResumeTemplateMapper;
import com.recruit_resume.service.FileResourceService;
import com.recruit_resume.service.ResumeTemplateService;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ResumeTemplateServiceImpl extends ServiceImpl<ResumeTemplateMapper, ResumeTemplate>
        implements ResumeTemplateService {

    private final FileResourceService fileResourceService;

    public ResumeTemplateServiceImpl(FileResourceService fileResourceService) {
        this.fileResourceService = fileResourceService;
    }

    @Override
    public List<ResumeTemplate> listActiveTemplates() {
        return list(new LambdaQueryWrapper<ResumeTemplate>()
                .eq(ResumeTemplate::getEnabled, 1)
                .orderByAsc(ResumeTemplate::getSortOrder)
                .orderByAsc(ResumeTemplate::getId))
                .stream()
                .map(this::withCoverUrl)
                .toList();
    }

    @Override
    public ResumeTemplate requireActiveTemplate(Long templateId) {
        if (templateId == null) {
            List<ResumeTemplate> activeTemplates = listActiveTemplates();
            if (activeTemplates.isEmpty()) {
                throw new BusinessException("No enabled resume template is available");
            }
            return activeTemplates.get(0);
        }
        ResumeTemplate template = getById(templateId);
        if (template == null || template.getEnabled() == null || template.getEnabled() != 1) {
            throw new BusinessException(ResultCode.NOT_FOUND);
        }
        return withCoverUrl(template);
    }

    @Override
    public List<ResumeTemplate> listForAdmin() {
        return list(new LambdaQueryWrapper<ResumeTemplate>()
                .orderByAsc(ResumeTemplate::getSortOrder)
                .orderByAsc(ResumeTemplate::getId))
                .stream()
                .map(this::withCoverUrl)
                .toList();
    }

    @Override
    public ResumeTemplate withCoverUrl(ResumeTemplate template) {
        if (template == null || template.getCoverFileId() == null) {
            return template;
        }
        FileResource cover = fileResourceService.getById(template.getCoverFileId());
        if (cover != null) {
            template.setCoverUrl(cover.getFileUrl());
        }
        return template;
    }
}
