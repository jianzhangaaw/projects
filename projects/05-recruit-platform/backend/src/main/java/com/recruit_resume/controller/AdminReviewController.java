package com.recruit_resume.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.recruit_resume.common.BusinessException;
import com.recruit_resume.common.Result;
import com.recruit_resume.entity.Company;
import com.recruit_resume.entity.CompanyDraft;
import com.recruit_resume.entity.Job;
import com.recruit_resume.entity.Notification;
import com.recruit_resume.service.CompanyDraftService;
import com.recruit_resume.service.CompanyService;
import com.recruit_resume.service.JobService;
import com.recruit_resume.service.NotificationService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.util.StringUtils;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

@Slf4j
@RestController
@RequestMapping("/api/admin/reviews")
public class AdminReviewController {

    private final CompanyService companyService;
    private final CompanyDraftService draftService;
    private final JobService jobService;
    private final NotificationService notificationService;

    public AdminReviewController(
            CompanyService companyService,
            CompanyDraftService draftService,
            JobService jobService,
            NotificationService notificationService
    ) {
        this.companyService = companyService;
        this.draftService = draftService;
        this.jobService = jobService;
        this.notificationService = notificationService;
    }

    @GetMapping("/companies")
    public Result<List<Company>> pendingCompanies() {
        List<Company> result = new ArrayList<>();

        List<CompanyDraft> drafts = draftService.list(new LambdaQueryWrapper<CompanyDraft>()
                .eq(CompanyDraft::getReviewStatus, "PENDING")
                .orderByDesc(CompanyDraft::getCreatedAt));
        Set<Long> draftCompanyIds = drafts.stream()
                .map(CompanyDraft::getCompanyId)
                .collect(Collectors.toSet());

        // 1. 新入驻审核：主表 PENDING，排除已有草稿的
        List<Company> newCompanies = companyService.list(new LambdaQueryWrapper<Company>()
                .eq(Company::getReviewStatus, "PENDING")
                .notIn(!draftCompanyIds.isEmpty(), Company::getId, draftCompanyIds)
                .orderByDesc(Company::getCreatedAt));
        for (Company c : newCompanies) {
            Company item = new Company();
            item.setId(c.getId());
            item.setUserId(c.getUserId());
            item.setCompanyName(c.getCompanyName());
            item.setIndustry(c.getIndustry());
            item.setCompanySize(c.getCompanySize());
            item.setContactName(c.getContactName());
            item.setContactPhone(c.getContactPhone());
            item.setDescription(c.getDescription());
            item.setLogoFileId(c.getLogoFileId());
            item.setReviewStatus(c.getReviewStatus());
            item.setCreatedAt(c.getCreatedAt());
            item.setReviewType("NEW_COMPANY");
            result.add(item);
        }

        // 2. 信息修改审核：草稿表 PENDING
        if (!drafts.isEmpty()) {
            Map<Long, Company> approvedMap = companyService.listByIds(draftCompanyIds).stream()
                    .collect(Collectors.toMap(Company::getId, c -> c, (a, b) -> a));
            for (CompanyDraft draft : drafts) {
                Company approved = approvedMap.get(draft.getCompanyId());
                if (approved == null) continue;

                Company item = new Company();
                item.setId(approved.getId());
                item.setUserId(approved.getUserId());
                item.setCompanyName(draft.getCompanyName());
                item.setIndustry(draft.getIndustry());
                item.setCompanySize(draft.getCompanySize());
                item.setContactName(draft.getContactName());
                item.setContactPhone(draft.getContactPhone());
                item.setDescription(draft.getDescription());
                item.setLogoFileId(draft.getLogoFileId());
                item.setReviewStatus("PENDING");
                item.setCreatedAt(draft.getCreatedAt());
                item.setReviewType("INFO_EDIT");

                item.setOldCompanyName(approved.getCompanyName());
                item.setOldIndustry(approved.getIndustry());
                item.setOldCompanySize(approved.getCompanySize());
                item.setOldContactName(approved.getContactName());
                item.setOldContactPhone(approved.getContactPhone());
                item.setOldDescription(approved.getDescription());

                result.add(item);
            }
        }

        return Result.success(result);
    }

    // ----- 原审批接口保持不变 -----
    @PatchMapping("/companies/{id}")
    public Result<Void> reviewCompany(@PathVariable Long id, @RequestParam String reviewStatus, @RequestParam(required = false) String reviewReason) {
        return doReviewCompany(id, reviewStatus, reviewReason);
    }

    @PutMapping("/companies/{id}")
    public Result<Void> reviewCompanyByPut(@PathVariable Long id, @RequestParam(required = false) String reviewStatus, @RequestParam(required = false) String status, @RequestParam(required = false) String reviewReason) {
        return doReviewCompany(id, StringUtils.hasText(reviewStatus) ? reviewStatus : status, reviewReason);
    }

    @PatchMapping("/companies/{id}/approve")
    public Result<Void> approveCompany(@PathVariable Long id) { return doReviewCompany(id, "APPROVED", null); }

    @PutMapping("/companies/{id}/approve")
    public Result<Void> approveCompanyByPut(@PathVariable Long id) { return doReviewCompany(id, "APPROVED", null); }

    @PatchMapping("/companies/{id}/reject")
    public Result<Void> rejectCompany(@PathVariable Long id, @RequestParam String reviewReason) { return doReviewCompany(id, "REJECTED", reviewReason); }

    @PutMapping("/companies/{id}/reject")
    public Result<Void> rejectCompanyByPut(@PathVariable Long id, @RequestParam String reviewReason) { return doReviewCompany(id, "REJECTED", reviewReason); }

    @GetMapping("/jobs")
    public Result<List<Job>> pendingJobs() {
        List<Job> jobs = jobService.list(new LambdaQueryWrapper<Job>()
                .eq(Job::getStatus, "PENDING")
                .orderByDesc(Job::getCreatedAt));
        if (jobs.isEmpty()) return Result.success(jobs);
        List<Long> companyIds = jobs.stream().map(Job::getCompanyId).filter(Objects::nonNull).distinct().toList();
        if (!companyIds.isEmpty()) {
            Map<Long, Company> companyMap = companyService.listByIds(companyIds).stream()
                    .collect(Collectors.toMap(Company::getId, c -> c, (a, b) -> a));
            jobs.forEach(job -> {
                Company c = companyMap.get(job.getCompanyId());
                if (c != null) {
                    job.setCompanyName(c.getCompanyName());
                    job.setIndustry(c.getIndustry());
                    job.setCompanySize(c.getCompanySize());
                    job.setLogoFileId(c.getLogoFileId());
                }
            });
        }
        return Result.success(jobs);
    }

    @PatchMapping("/jobs/{id}") public Result<Void> reviewJob(@PathVariable Long id, @RequestParam String status, @RequestParam(required = false) String reviewReason) { return doReviewJob(id, status, reviewReason); }
    @PutMapping("/jobs/{id}") public Result<Void> reviewJobByPut(@PathVariable Long id, @RequestParam String status, @RequestParam(required = false) String reviewReason) { return doReviewJob(id, status, reviewReason); }
    @PatchMapping("/jobs/{id}/approve") public Result<Void> approveJob(@PathVariable Long id) { return doReviewJob(id, "PUBLISHED", null); }
    @PutMapping("/jobs/{id}/approve") public Result<Void> approveJobByPut(@PathVariable Long id) { return doReviewJob(id, "PUBLISHED", null); }
    @PatchMapping("/jobs/{id}/reject") public Result<Void> rejectJob(@PathVariable Long id, @RequestParam String reviewReason) { return doReviewJob(id, "REJECTED", reviewReason); }
    @PutMapping("/jobs/{id}/reject") public Result<Void> rejectJobByPut(@PathVariable Long id, @RequestParam String reviewReason) { return doReviewJob(id, "REJECTED", reviewReason); }

    // ---------- private ----------

    private Result<Void> doReviewCompany(Long id, String reviewStatus, String reviewReason) {
        Company existing = companyService.getById(id);
        if (existing == null) throw new BusinessException("企业不存在");
        if (!"APPROVED".equals(reviewStatus) && !"REJECTED".equals(reviewStatus))
            throw new BusinessException("企业审核状态只能是 APPROVED 或 REJECTED");
        if ("REJECTED".equals(reviewStatus) && !StringUtils.hasText(reviewReason))
            throw new BusinessException("驳回企业时必须填写原因");

        CompanyDraft draft = draftService.getOne(new LambdaQueryWrapper<CompanyDraft>()
                .eq(CompanyDraft::getCompanyId, id)
                .eq(CompanyDraft::getReviewStatus, "PENDING")
                .last("limit 1"));

        if (draft != null) {
            if ("APPROVED".equals(reviewStatus)) {
                existing.setCompanyName(draft.getCompanyName());
                existing.setIndustry(draft.getIndustry());
                existing.setCompanySize(draft.getCompanySize());
                existing.setContactName(draft.getContactName());
                existing.setContactPhone(draft.getContactPhone());
                existing.setDescription(draft.getDescription());
                existing.setLogoFileId(draft.getLogoFileId());
                existing.setReviewStatus("APPROVED");
                existing.setReviewReason(reviewReason);
                companyService.updateById(existing);
                draftService.removeById(draft.getId());
                log.info("信息修改审核通过: companyId={}", id);
            } else {
                draft.setReviewStatus("REJECTED");
                draft.setReviewReason(reviewReason);
                draftService.updateById(draft);
                log.info("信息修改审核驳回: companyId={}", id);
            }
            createNotification(existing.getUserId(), "企业信息修改审核结果",
                    "APPROVED".equals(reviewStatus) ? "你的企业信息修改已通过审核" : "你的企业信息修改已被驳回，原因：" + reviewReason, "REVIEW");
            return Result.success();
        }

        Company company = new Company();
        company.setId(id);
        company.setReviewStatus(reviewStatus);
        company.setReviewReason(reviewReason);
        companyService.updateById(company);

        createNotification(existing.getUserId(), "企业入驻审核结果",
                "APPROVED".equals(reviewStatus) ? "你的企业入驻申请已通过审核" : "你的企业入驻申请已被驳回，原因：" + reviewReason, "REVIEW");
        log.info("企业审核完成: companyId={}, status={}, reason={}", id, reviewStatus, reviewReason);
        return Result.success();
    }

    private Result<Void> doReviewJob(Long id, String status, String reviewReason) {
        Job existing = jobService.getById(id);
        if (existing == null) throw new BusinessException("岗位不存在");
        if (!"PUBLISHED".equals(status) && !"REJECTED".equals(status))
            throw new BusinessException("岗位审核状态只能是 PUBLISHED 或 REJECTED");
        if ("REJECTED".equals(status) && !StringUtils.hasText(reviewReason))
            throw new BusinessException("驳回岗位时必须填写原因");
        Job job = new Job();
        job.setId(id);
        job.setStatus(status);
        job.setReviewReason(reviewReason);
        jobService.updateById(job);
        Company company = companyService.getById(existing.getCompanyId());
        if (company != null) {
            createNotification(company.getUserId(), "岗位审核结果",
                    "PUBLISHED".equals(status) ? "你的岗位【" + existing.getJobName() + "】已通过审核并发布" : "你的岗位【" + existing.getJobName() + "】已被驳回，原因：" + reviewReason, "REVIEW");
        }
        log.info("岗位审核完成: jobId={}, jobName={}, status={}, reason={}", id, existing.getJobName(), status, reviewReason);
        return Result.success();
    }

    private void createNotification(Long receiverId, String title, String content, String type) {
        if (receiverId == null) return;
        Notification notification = new Notification();
        notification.setReceiverId(receiverId);
        notification.setTitle(title);
        notification.setContent(content);
        notification.setType(type);
        notification.setIsRead(0);
        notificationService.save(notification);
    }
}
