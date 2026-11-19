package com.recruit_resume.service;

import com.recruit_resume.common.BusinessException;
import com.recruit_resume.dto.ResumeGenerationSnapshot;
import com.recruit_resume.entity.ResumeTemplate;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.thymeleaf.TemplateEngine;
import org.thymeleaf.context.Context;

import java.util.Locale;

@Service
public class ResumeHtmlRenderService {

    private final TemplateEngine templateEngine;

    public ResumeHtmlRenderService(TemplateEngine templateEngine) {
        this.templateEngine = templateEngine;
    }

    public String render(ResumeTemplate template, ResumeGenerationSnapshot snapshot) {
        if (template == null || !StringUtils.hasText(template.getTemplateCode())) {
            throw new BusinessException("Resume template is invalid");
        }
        String templateCode = template.getTemplateCode();
        if (!templateCode.matches("[a-zA-Z0-9_-]+")) {
            throw new BusinessException("Resume template code is invalid");
        }
        Context context = new Context(Locale.CHINA);
        context.setVariable("template", template);
        context.setVariable("snapshot", snapshot);
        context.setVariable("profile", snapshot.getProfile());
        context.setVariable("skills", snapshot.getSkills());
        context.setVariable("experiences", snapshot.getExperiences());
        return templateEngine.process("resumes/" + templateCode, context);
    }
}
