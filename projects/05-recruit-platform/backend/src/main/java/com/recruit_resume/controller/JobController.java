package com.recruit_resume.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.recruit_resume.common.Result;
import com.recruit_resume.common.PageQuery;
import com.recruit_resume.entity.Company;
import com.recruit_resume.entity.Job;
import com.recruit_resume.service.CompanyService;
import com.recruit_resume.service.JobService;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/jobs")
public class JobController extends BaseCrudController<Job> {

    private final JobService service;
    private final CompanyService companyService;

    public JobController(JobService service, CompanyService companyService) {
        super(service);
        this.service = service;
        this.companyService = companyService;
    }

    @GetMapping("/published")
    public Result<IPage<Job>> published(
            PageQuery query,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String city,
            @RequestParam(required = false) String jobType
    ) {
        LambdaQueryWrapper<Job> wrapper = new LambdaQueryWrapper<Job>()
                .eq(Job::getStatus, "PUBLISHED")
                .like(StringUtils.hasText(keyword), Job::getJobName, keyword)
                .eq(StringUtils.hasText(city), Job::getCity, city)
                .eq(StringUtils.hasText(jobType), Job::getJobType, jobType)
                .orderByDesc(Job::getCreatedAt);
        IPage<Job> page = service.page(Page.of(query.getCurrent(), query.getSize()), wrapper);
        fillCompanyInfo(page.getRecords());
        return Result.success(page);
    }

    @GetMapping("/by-company")
    public Result<List<Job>> listByCompany(@RequestParam Long companyId) {
        return Result.success(service.list(new LambdaQueryWrapper<Job>()
                .eq(Job::getCompanyId, companyId)
                .orderByDesc(Job::getUpdatedAt)));
    }

    private void fillCompanyInfo(List<Job> jobs) {
        List<Long> companyIds = jobs.stream()
                .map(Job::getCompanyId)
                .filter(id -> id != null)
                .distinct()
                .toList();
        if (companyIds.isEmpty()) {
            return;
        }
        Map<Long, Company> companyById = companyService.listByIds(companyIds).stream()
                .collect(Collectors.toMap(Company::getId, Function.identity()));

        for (Job job : jobs) {
            Company company = companyById.get(job.getCompanyId());
            if (company == null) {
                continue;
            }
            job.setCompanyName(company.getCompanyName());
            job.setIndustry(company.getIndustry());
            job.setCompanySize(company.getCompanySize());
        }
    }

    @PatchMapping("/{id}/status")
    public Result<Void> updateStatus(@PathVariable Long id, @RequestParam String status) {
        Job job = new Job();
        job.setId(id);
        job.setStatus(status);
        if (!"REJECTED".equals(status)) {
            job.setReviewReason(null);
        }
        service.updateById(job);
        return Result.success();
    }
}
