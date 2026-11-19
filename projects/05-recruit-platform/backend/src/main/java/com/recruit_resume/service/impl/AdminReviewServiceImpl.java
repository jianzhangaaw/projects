package com.recruit_resume.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.recruit_resume.common.BusinessException;
import com.recruit_resume.entity.Company;
import com.recruit_resume.entity.CompanyDraft;
import com.recruit_resume.entity.Job;
import com.recruit_resume.entity.Notification;
import com.recruit_resume.service.AdminReviewService;
import com.recruit_resume.service.CompanyDraftService;
import com.recruit_resume.service.CompanyService;
import com.recruit_resume.service.JobService;
import com.recruit_resume.service.NotificationService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

@Slf4j
@Service
public class AdminReviewServiceImpl implements AdminReviewService {

    private static final Set<String> COMPANY_DECISIONS = Set.of("APPROVED", "REJECTED");
    private static final Set<String> JOB_DECISIONS = Set.of("PUBLISHED", "REJECTED");

    private final CompanyService companyService;
    private final CompanyDraftService draftService;
    private final JobService jobService;
    private final NotificationService notificationService;

    public AdminReviewServiceImpl(
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

    // ------------------------------------------------------------------ 查询

    @Override
    public List<Company> pendingCompanies() {
        List<CompanyDraft> drafts = draftService.list(new LambdaQueryWrapper<CompanyDraft>()
                .eq(CompanyDraft::getReviewStatus, "PENDING")
                .orderByDesc(CompanyDraft::getCreatedAt));
        Set<Long> draftCompanyIds = drafts.stream()
                .map(CompanyDraft::getCompanyId)
                .filter(Objects::nonNull)
                .collect(Collectors.toSet());

        // 1. 新入驻：主表 PENDING，且没有待审草稿（有草稿说明是"资料修改"）
        List<Company> result = new ArrayList<>();
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

        // 2. 资料修改：草稿 PENDING，展示时把草稿内容与主表的旧值并排放，方便对比
        if (!drafts.isEmpty()) {
            Map<Long, Company> approvedMap = new HashMap<>();
            for (Company c : companyService.listByIds(draftCompanyIds)) {
                approvedMap.put(c.getId(), c);
            }
            for (CompanyDraft draft : drafts) {
                Company approved = approvedMap.get(draft.getCompanyId());
                if (approved == null) {
                    continue;
                }
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
        return result;
    }

    @Override
    public List<Job> pendingJobs() {
        List<Job> jobs = jobService.list(new LambdaQueryWrapper<Job>()
                .eq(Job::getStatus, "PENDING")
                .orderByDesc(Job::getCreatedAt));
        if (jobs.isEmpty()) {
            return jobs;
        }
        List<Long> companyIds = jobs.stream().map(Job::getCompanyId).filter(Objects::nonNull).distinct().toList();
        if (companyIds.isEmpty()) {
            return jobs;
        }
        Map<Long, Company> companyMap = new HashMap<>();
        for (Company c : companyService.listByIds(companyIds)) {
            companyMap.put(c.getId(), c);
        }
        for (Job job : jobs) {
            Company c = companyMap.get(job.getCompanyId());
            if (c != null) {
                job.setCompanyName(c.getCompanyName());
                job.setIndustry(c.getIndustry());
                job.setCompanySize(c.getCompanySize());
                job.setLogoFileId(c.getLogoFileId());
            }
        }
        return jobs;
    }

    // ------------------------------------------------------------------ 审核

    @Override
    @Transactional
    public void reviewCompany(Long companyId, String decision, String reason) {
        if (!COMPANY_DECISIONS.contains(decision)) {
            throw new BusinessException("企业审核状态只能是 APPROVED 或 REJECTED");
        }
        if ("REJECTED".equals(decision) && !StringUtils.hasText(reason)) {
            throw new BusinessException("驳回企业时必须填写原因");
        }
        Company existing = companyService.getById(companyId);
        if (existing == null) {
            throw new BusinessException("企业不存在");
        }

        CompanyDraft draft = draftService.getOne(new LambdaQueryWrapper<CompanyDraft>()
                .eq(CompanyDraft::getCompanyId, companyId)
                .eq(CompanyDraft::getReviewStatus, "PENDING")
                .last("limit 1"));

        if (draft != null) {
            reviewCompanyDraft(existing, draft, decision, reason);
            return;
        }

        // 新入驻审核：只允许从 PENDING 出发，防止对已通过的企业重复「审核」
        if (!"PENDING".equals(existing.getReviewStatus())) {
            throw new BusinessException("该企业当前状态是 " + existing.getReviewStatus() + "，无需再次审核");
        }
        // 通过时把上一次的驳回原因清掉，否则前端会显示「已通过，原因：材料不全」。
        // updateById 默认跳过 null 字段，所以这里用 UpdateWrapper 显式 set(null)。
        companyService.update(new LambdaUpdateWrapper<Company>()
                .eq(Company::getId, companyId)
                .set(Company::getReviewStatus, decision)
                .set(Company::getReviewReason, "REJECTED".equals(decision) ? reason : null));

        notifyCompany(existing.getUserId(),
                "APPROVED".equals(decision)
                        ? "你的企业入驻申请已通过审核"
                        : "你的企业入驻申请已被驳回，原因：" + reason);
        log.info("企业入驻审核完成: companyId={}, status={}, reason={}", companyId, decision, reason);
    }

    private void reviewCompanyDraft(Company company, CompanyDraft draft, String decision, String reason) {
        if ("APPROVED".equals(decision)) {
            // updateById 默认跳过 null 字段，清空 reviewReason 必须用 UpdateWrapper 显式 set(null)
            companyService.update(new LambdaUpdateWrapper<Company>()
                    .eq(Company::getId, company.getId())
                    .set(Company::getCompanyName, draft.getCompanyName())
                    .set(Company::getIndustry, draft.getIndustry())
                    .set(Company::getCompanySize, draft.getCompanySize())
                    .set(Company::getContactName, draft.getContactName())
                    .set(Company::getContactPhone, draft.getContactPhone())
                    .set(Company::getDescription, draft.getDescription())
                    .set(Company::getLogoFileId, draft.getLogoFileId())
                    .set(Company::getReviewStatus, "APPROVED")
                    .set(Company::getReviewReason, null));
            // 草稿与通知在同一个事务里：删草稿失败会连主表更新一起回滚
            draftService.removeById(draft.getId());
            log.info("企业资料修改审核通过: companyId={}", company.getId());
        } else {
            draft.setReviewStatus("REJECTED");
            draft.setReviewReason(reason);
            draftService.updateById(draft);
            log.info("企业资料修改审核驳回: companyId={}", company.getId());
        }
        notifyCompany(company.getUserId(),
                "APPROVED".equals(decision)
                        ? "你的企业信息修改已通过审核"
                        : "你的企业信息修改已被驳回，原因：" + reason);
    }

    @Override
    @Transactional
    public void reviewJob(Long jobId, String decision, String reason) {
        if (!JOB_DECISIONS.contains(decision)) {
            throw new BusinessException("岗位审核状态只能是 PUBLISHED 或 REJECTED");
        }
        if ("REJECTED".equals(decision) && !StringUtils.hasText(reason)) {
            throw new BusinessException("驳回岗位时必须填写原因");
        }
        Job existing = jobService.getById(jobId);
        if (existing == null) {
            throw new BusinessException("岗位不存在");
        }
        if (!"PENDING".equals(existing.getStatus())) {
            throw new BusinessException("该岗位当前状态是 " + existing.getStatus() + "，不能审核");
        }

        jobService.update(new LambdaUpdateWrapper<Job>()
                .eq(Job::getId, jobId)
                .set(Job::getStatus, decision)
                .set(Job::getReviewReason, "REJECTED".equals(decision) ? reason : null));

        Company company = companyService.getById(existing.getCompanyId());
        if (company != null && company.getUserId() != null) {
            notifyCompany(company.getUserId(),
                    "PUBLISHED".equals(decision)
                            ? "你的岗位【" + existing.getJobName() + "】已通过审核并发布"
                            : "你的岗位【" + existing.getJobName() + "】已被驳回，原因：" + reason);
        }
        log.info("岗位审核完成: jobId={}, jobName={}, status={}, reason={}",
                jobId, existing.getJobName(), decision, reason);
    }

    private void notifyCompany(Long receiverId, String content) {
        if (receiverId == null) {
            return;
        }
        Notification n = new Notification();
        n.setReceiverId(receiverId);
        n.setTitle("审核结果");
        n.setContent(content);
        n.setType("REVIEW");
        n.setIsRead(0);
        notificationService.save(n);
    }
}
