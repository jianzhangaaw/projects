package com.recruit_resume.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.recruit_resume.common.BusinessException;
import com.recruit_resume.common.PageQuery;
import com.recruit_resume.common.Result;
import com.recruit_resume.common.ResultCode;
import com.recruit_resume.dto.CompanyApplicationDetail;
import com.recruit_resume.dto.StudentApplicationDetail;
import com.recruit_resume.entity.JobApplication;
import com.recruit_resume.security.CurrentUser;
import com.recruit_resume.security.CurrentUserContext;
import com.recruit_resume.service.JobApplicationService;
import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * 投递接口。业务逻辑（校验、状态机、事务、通知）都在 {@link JobApplicationService} 里，
 * 这里只负责解析参数、做角色门禁、把结果包成 {@link Result}。
 */
@Slf4j
@RestController
@RequestMapping("/api/applications")
public class JobApplicationController {

    private final JobApplicationService service;

    public JobApplicationController(JobApplicationService service) {
        this.service = service;
    }

    @GetMapping
    public Result<IPage<JobApplication>> page(@Valid PageQuery query) {
        CurrentUser user = CurrentUserContext.require();
        return Result.success(service.pageForUser(user.getUserId(), user.getRole(),
                query.getCurrent(), query.getSize()));
    }

    @PostMapping
    public Result<JobApplication> create(@RequestBody JobApplication body) {
        CurrentUser user = CurrentUserContext.require();
        if (!"STUDENT".equals(user.getRole())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        return Result.success(service.apply(user.getUserId(), body.getJobId(), body.getResumeId()));
    }

    @GetMapping("/by-student")
    public Result<List<JobApplication>> listByStudent(@RequestParam(required = false) Long studentId) {
        CurrentUser user = CurrentUserContext.require();
        if ("ADMIN".equals(user.getRole())) {
            if (studentId == null) {
                throw new BusinessException("studentId 不能为空");
            }
            return Result.success(service.list(new LambdaQueryWrapper<JobApplication>()
                    .eq(JobApplication::getStudentId, studentId)
                    .orderByDesc(JobApplication::getCreatedAt)));
        }
        return Result.success(service.listByStudent(user.getUserId()));
    }

    @GetMapping("/by-student/detail")
    public Result<List<StudentApplicationDetail>> listStudentDetails() {
        return Result.success(service.listStudentDetails(CurrentUserContext.userId()));
    }

    @GetMapping("/by-company")
    public Result<List<JobApplication>> listByCompany(@RequestParam(required = false) Long companyId) {
        CurrentUser user = CurrentUserContext.require();
        if ("ADMIN".equals(user.getRole())) {
            if (companyId == null) {
                throw new BusinessException("companyId 不能为空");
            }
            return Result.success(service.list(new LambdaQueryWrapper<JobApplication>()
                    .eq(JobApplication::getCompanyId, companyId)
                    .orderByDesc(JobApplication::getCreatedAt)));
        }
        if (!"COMPANY".equals(user.getRole())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        return Result.success(service.listByCompany(user.getUserId()));
    }

    @GetMapping("/by-company/detail")
    public Result<List<CompanyApplicationDetail>> listCompanyDetails() {
        return Result.success(service.listCompanyDetails(CurrentUserContext.userId()));
    }

    @PatchMapping("/{id}/status")
    public Result<Void> updateStatus(
            @PathVariable Long id,
            @RequestParam String status,
            @RequestParam(required = false) String remark
    ) {
        return doUpdateStatus(id, status, remark);
    }

    /** 保留 PUT 版本，前端历史调用用的是它。 */
    @PutMapping("/{id}/status")
    public Result<Void> updateStatusByPut(
            @PathVariable Long id,
            @RequestParam String status,
            @RequestParam(required = false) String remark
    ) {
        return doUpdateStatus(id, status, remark);
    }

    @DeleteMapping("/{id}")
    public Result<Void> withdraw(@PathVariable Long id) {
        CurrentUser user = CurrentUserContext.require();
        if (!"STUDENT".equals(user.getRole())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        service.withdraw(user.getUserId(), id);
        return Result.success();
    }

    private Result<Void> doUpdateStatus(Long id, String status, String remark) {
        CurrentUser user = CurrentUserContext.require();
        service.updateStatus(user.getUserId(), user.getRole(), id, status, remark);
        return Result.success();
    }
}
