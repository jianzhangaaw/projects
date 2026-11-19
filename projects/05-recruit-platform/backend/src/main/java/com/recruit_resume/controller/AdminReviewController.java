package com.recruit_resume.controller;

import com.recruit_resume.common.Result;
import com.recruit_resume.entity.Company;
import com.recruit_resume.entity.Job;
import com.recruit_resume.service.AdminReviewService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * 管理员审核接口。审核逻辑（事务、状态机、通知）在 {@link AdminReviewService} 里。
 *
 * <p>每个动作同时提供 PATCH 与 PUT 两个入口，是早期前端调用不统一留下的兼容层，
 * 内部都走同一个 Service 方法。
 */
@Slf4j
@RestController
@RequestMapping("/api/admin/reviews")
public class AdminReviewController {

    private final AdminReviewService reviewService;

    public AdminReviewController(AdminReviewService reviewService) {
        this.reviewService = reviewService;
    }

    @GetMapping("/companies")
    public Result<List<Company>> pendingCompanies() {
        return Result.success(reviewService.pendingCompanies());
    }

    @GetMapping("/jobs")
    public Result<List<Job>> pendingJobs() {
        return Result.success(reviewService.pendingJobs());
    }

    @PatchMapping("/companies/{id}")
    public Result<Void> reviewCompany(
            @PathVariable Long id,
            @RequestParam String reviewStatus,
            @RequestParam(required = false) String reviewReason
    ) {
        reviewService.reviewCompany(id, reviewStatus, reviewReason);
        return Result.success();
    }

    @PutMapping("/companies/{id}")
    public Result<Void> reviewCompanyByPut(
            @PathVariable Long id,
            @RequestParam(required = false) String reviewStatus,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String reviewReason
    ) {
        reviewService.reviewCompany(id, StringUtils.hasText(reviewStatus) ? reviewStatus : status, reviewReason);
        return Result.success();
    }

    @PatchMapping("/companies/{id}/approve")
    public Result<Void> approveCompany(@PathVariable Long id) {
        reviewService.reviewCompany(id, "APPROVED", null);
        return Result.success();
    }

    @PutMapping("/companies/{id}/approve")
    public Result<Void> approveCompanyByPut(@PathVariable Long id) {
        reviewService.reviewCompany(id, "APPROVED", null);
        return Result.success();
    }

    @PatchMapping("/companies/{id}/reject")
    public Result<Void> rejectCompany(@PathVariable Long id, @RequestParam String reviewReason) {
        reviewService.reviewCompany(id, "REJECTED", reviewReason);
        return Result.success();
    }

    @PutMapping("/companies/{id}/reject")
    public Result<Void> rejectCompanyByPut(@PathVariable Long id, @RequestParam String reviewReason) {
        reviewService.reviewCompany(id, "REJECTED", reviewReason);
        return Result.success();
    }

    @PatchMapping("/jobs/{id}")
    public Result<Void> reviewJob(
            @PathVariable Long id,
            @RequestParam String status,
            @RequestParam(required = false) String reviewReason
    ) {
        reviewService.reviewJob(id, status, reviewReason);
        return Result.success();
    }

    @PutMapping("/jobs/{id}")
    public Result<Void> reviewJobByPut(
            @PathVariable Long id,
            @RequestParam String status,
            @RequestParam(required = false) String reviewReason
    ) {
        reviewService.reviewJob(id, status, reviewReason);
        return Result.success();
    }

    @PatchMapping("/jobs/{id}/approve")
    public Result<Void> approveJob(@PathVariable Long id) {
        reviewService.reviewJob(id, "PUBLISHED", null);
        return Result.success();
    }

    @PutMapping("/jobs/{id}/approve")
    public Result<Void> approveJobByPut(@PathVariable Long id) {
        reviewService.reviewJob(id, "PUBLISHED", null);
        return Result.success();
    }

    @PatchMapping("/jobs/{id}/reject")
    public Result<Void> rejectJob(@PathVariable Long id, @RequestParam String reviewReason) {
        reviewService.reviewJob(id, "REJECTED", reviewReason);
        return Result.success();
    }

    @PutMapping("/jobs/{id}/reject")
    public Result<Void> rejectJobByPut(@PathVariable Long id, @RequestParam String reviewReason) {
        reviewService.reviewJob(id, "REJECTED", reviewReason);
        return Result.success();
    }
}
