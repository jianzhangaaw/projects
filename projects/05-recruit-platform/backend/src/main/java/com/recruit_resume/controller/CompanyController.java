package com.recruit_resume.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.recruit_resume.common.BusinessException;
import com.recruit_resume.common.Result;
import com.recruit_resume.entity.Company;
import com.recruit_resume.entity.CompanyDraft;
import com.recruit_resume.service.CompanyDraftService;
import com.recruit_resume.service.CompanyService;
import org.springframework.web.bind.annotation.PatchMapping;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/company/companies")
@Slf4j
public class CompanyController extends BaseCrudController<Company> {

    private final CompanyService service;
    private final CompanyDraftService draftService;

    public CompanyController(CompanyService service, CompanyDraftService draftService) {
        super(service);
        this.service = service;
        this.draftService = draftService;
    }

    @GetMapping("/mine")
    public Result<Company> mine(@RequestParam Long userId) {
        Company company = service.getOne(new LambdaQueryWrapper<Company>()
                .eq(Company::getUserId, userId)
                .last("limit 1"));
        return Result.success(company);
    }

    @GetMapping("/mine/draft")
    public Result<CompanyDraft> mineDraft(@RequestParam Long userId) {
        Company company = service.getOne(new LambdaQueryWrapper<Company>()
                .eq(Company::getUserId, userId)
                .last("limit 1"));
        if (company == null) return Result.success(null);
        CompanyDraft draft = draftService.getOne(new LambdaQueryWrapper<CompanyDraft>()
                .eq(CompanyDraft::getCompanyId, company.getId())
                .last("limit 1"));
        return Result.success(draft);
    }

    @PostMapping("/mine")
    public Result<Company> saveMine(@RequestParam Long userId, @RequestBody Company body) {
        Company existing = service.getOne(new LambdaQueryWrapper<Company>()
                .eq(Company::getUserId, userId)
                .last("limit 1"));
        body.setUserId(userId);

        // 新企业
        if (existing == null) {
            body.setReviewStatus("PENDING");
            service.save(body);
            return Result.success(body);
        }

        // 已审批 → 草稿表
        if ("APPROVED".equals(existing.getReviewStatus())) {
            CompanyDraft draft = draftService.getOne(new LambdaQueryWrapper<CompanyDraft>()
                    .eq(CompanyDraft::getCompanyId, existing.getId()).last("limit 1"));
            if (draft == null) { draft = new CompanyDraft(); draft.setCompanyId(existing.getId()); }
            draft.setCompanyName(body.getCompanyName());
            draft.setIndustry(body.getIndustry());
            draft.setCompanySize(body.getCompanySize());
            draft.setContactName(body.getContactName());
            draft.setContactPhone(body.getContactPhone());
            draft.setDescription(body.getDescription());
            draft.setLogoFileId(body.getLogoFileId());
            draft.setReviewStatus("PENDING");
            draft.setReviewReason(null);
            draftService.saveOrUpdate(draft);
            return Result.success(service.getById(existing.getId()));
        }

        // 初次审核中 → 主表
        service.update(new LambdaUpdateWrapper<Company>()
                .eq(Company::getId, existing.getId())
                .set(Company::getCompanyName, body.getCompanyName())
                .set(Company::getIndustry, body.getIndustry())
                .set(Company::getCompanySize, body.getCompanySize())
                .set(Company::getContactName, body.getContactName())
                .set(Company::getContactPhone, body.getContactPhone())
                .set(Company::getDescription, body.getDescription())
                .set(Company::getLogoFileId, body.getLogoFileId())
                .set(Company::getReviewStatus, "PENDING")
                .set(Company::getReviewReason, (String) null));
        return Result.success(service.getById(existing.getId()));
    }

    @PatchMapping("/mine/logo")
    public Result<Company> updateLogo(@RequestParam Long userId, @RequestParam Long logoFileId) {
        Company existing = service.getOne(new LambdaQueryWrapper<Company>()
                .eq(Company::getUserId, userId).last("limit 1"));
        if (existing == null) throw new BusinessException("请先保存企业基本信息");
        if ("APPROVED".equals(existing.getReviewStatus())) {
            CompanyDraft draft = draftService.getOne(new LambdaQueryWrapper<CompanyDraft>()
                    .eq(CompanyDraft::getCompanyId, existing.getId()).last("limit 1"));
            if (draft == null) { draft = new CompanyDraft(); draft.setCompanyId(existing.getId()); draft.setReviewStatus("PENDING"); }
            draft.setLogoFileId(logoFileId);
            draftService.saveOrUpdate(draft);
            return Result.success(service.getById(existing.getId()));
        }
        service.update(new LambdaUpdateWrapper<Company>().eq(Company::getId, existing.getId()).set(Company::getLogoFileId, logoFileId));
        return Result.success(service.getById(existing.getId()));
    }
}
