package com.recruit_resume.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.recruit_resume.common.BusinessException;
import com.recruit_resume.common.Result;
import com.recruit_resume.common.ResultCode;
import com.recruit_resume.entity.Company;
import com.recruit_resume.entity.CompanyDraft;
import com.recruit_resume.security.CurrentUser;
import com.recruit_resume.security.CurrentUserContext;
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

    /**
     * 历史接口都收 {@code userId} 参数，早期直接拿它查库（改个参数就能读别人）。
     * 现在参数只为兼容旧前端保留：传了就必须等于当前登录用户，不传就用当前用户。
     * 下一阶段会把参数彻底删掉。
     */
    private Long resolveUserId(Long requestedUserId) {
        Long currentUserId = CurrentUserContext.userId();
        if (requestedUserId != null && !requestedUserId.equals(currentUserId)) {
            log.warn("企业信息接口越权尝试: currentUserId={}, requestedUserId={}", currentUserId, requestedUserId);
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        return currentUserId;
    }

    @Override
    protected boolean isOwnedBy(Company entity, CurrentUser user) {
        return entity.getUserId() != null && entity.getUserId().equals(user.getUserId());
    }

    /**
     * 建企业资料。原来走 BaseCrud 的 create，userId 与 reviewStatus 都来自请求体，
     * 企业可以直接把自己建到别人名下、或者自封 APPROVED。这里强制用当前用户、强制待审。
     */
    @Override
    @org.springframework.web.bind.annotation.PostMapping
    public Result<Company> create(@org.springframework.web.bind.annotation.RequestBody Company body) {
        Long userId = CurrentUserContext.userId();
        body.setId(null);
        body.setUserId(userId);
        body.setReviewStatus("PENDING");
        body.setReviewReason(null);
        service.save(body);
        return Result.success(body);
    }

    @GetMapping("/mine")
    public Result<Company> mine(@RequestParam(required = false) Long userId) {
        Long currentUserId = resolveUserId(userId);
        Company company = service.getOne(new LambdaQueryWrapper<Company>()
                .eq(Company::getUserId, currentUserId)
                .last("limit 1"));
        return Result.success(company);
    }

    @GetMapping("/mine/draft")
    public Result<CompanyDraft> mineDraft(@RequestParam(required = false) Long userId) {
        Long currentUserId = resolveUserId(userId);
        Company company = service.getOne(new LambdaQueryWrapper<Company>()
                .eq(Company::getUserId, currentUserId)
                .last("limit 1"));
        if (company == null) return Result.success(null);
        CompanyDraft draft = draftService.getOne(new LambdaQueryWrapper<CompanyDraft>()
                .eq(CompanyDraft::getCompanyId, company.getId())
                .last("limit 1"));
        return Result.success(draft);
    }

    @PostMapping("/mine")
    public Result<Company> saveMine(@RequestParam(required = false) Long userId, @RequestBody Company body) {
        Long currentUserId = resolveUserId(userId);
        Company existing = service.getOne(new LambdaQueryWrapper<Company>()
                .eq(Company::getUserId, currentUserId)
                .last("limit 1"));
        body.setUserId(currentUserId);
        body.setId(existing == null ? null : existing.getId());

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
            if (draft.getId() == null) {
                draftService.save(draft);
            } else {
                // 重新提交时清空上一次的驳回原因；saveOrUpdate 走 updateById 会跳过 null
                draftService.update(new LambdaUpdateWrapper<CompanyDraft>()
                        .eq(CompanyDraft::getId, draft.getId())
                        .set(CompanyDraft::getReviewStatus, "PENDING")
                        .set(CompanyDraft::getReviewReason, null));
            }
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
    public Result<Company> updateLogo(
            @RequestParam(required = false) Long userId,
            @RequestParam Long logoFileId
    ) {
        Long currentUserId = resolveUserId(userId);
        Company existing = service.getOne(new LambdaQueryWrapper<Company>()
                .eq(Company::getUserId, currentUserId).last("limit 1"));
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
