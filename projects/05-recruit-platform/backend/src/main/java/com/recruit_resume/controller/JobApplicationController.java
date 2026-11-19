package com.recruit_resume.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.recruit_resume.common.BusinessException;
import com.recruit_resume.common.PageQuery;
import com.recruit_resume.common.Result;
import com.recruit_resume.common.ResultCode;
import com.recruit_resume.dto.CompanyApplicationDetail;
import com.recruit_resume.dto.StudentApplicationDetail;
import com.recruit_resume.entity.Company;
import com.recruit_resume.entity.Job;
import com.recruit_resume.entity.JobApplication;
import com.recruit_resume.entity.Notification;
import com.recruit_resume.entity.Resume;
import com.recruit_resume.entity.StudentProfile;
import com.recruit_resume.security.CurrentUser;
import com.recruit_resume.security.CurrentUserContext;
import com.recruit_resume.service.CompanyService;
import com.recruit_resume.service.JobApplicationService;
import com.recruit_resume.service.JobService;
import com.recruit_resume.service.NotificationService;
import com.recruit_resume.service.ResumeService;
import com.recruit_resume.service.StudentProfileService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import lombok.extern.slf4j.Slf4j;

import java.util.List;

@Slf4j
@RestController
@RequestMapping("/api/applications")
public class JobApplicationController {

    private final JobApplicationService service;
    private final JobService jobService;
    private final CompanyService companyService;
    private final StudentProfileService studentProfileService;
    private final ResumeService resumeService;
    private final NotificationService notificationService;

    public JobApplicationController(
            JobApplicationService service,
            JobService jobService,
            CompanyService companyService,
            StudentProfileService studentProfileService,
            ResumeService resumeService,
            NotificationService notificationService
    ) {
        this.service = service;
        this.jobService = jobService;
        this.companyService = companyService;
        this.studentProfileService = studentProfileService;
        this.resumeService = resumeService;
        this.notificationService = notificationService;
    }

    @GetMapping
    public Result<IPage<JobApplication>> page(@Valid PageQuery query) {
        return Result.success(service.page(Page.of(query.getCurrent(), query.getSize()), scopedWrapper()));
    }

    @PostMapping
    public Result<JobApplication> create(@RequestBody JobApplication body) {
        CurrentUser currentUser = CurrentUserContext.require();
        if (!"STUDENT".equals(currentUser.getRole())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        StudentProfile student = currentStudentProfile();
        Job job = jobService.getById(body.getJobId());
        if (job == null || !"PUBLISHED".equals(job.getStatus())) {
            throw new BusinessException("岗位不存在或未发布");
        }
        Company company = companyService.getById(job.getCompanyId());
        if (company == null) {
            throw new BusinessException("岗位所属企业不存在");
        }
        // 防止学生投递时附带他人简历：resumeId 必须属于当前学生
        if (body.getResumeId() != null) {
            Resume resume = resumeService.getById(body.getResumeId());
            if (resume == null) {
                throw new BusinessException("所选简历不存在");
            }
            if (!student.getId().equals(resume.getStudentId())) {
                throw new BusinessException(ResultCode.FORBIDDEN.getCode(), "只能投递自己的简历");
            }
        }
        // 防止同一学生对同一岗位重复投递刷屏企业通知
        long alreadyApplied = service.count(new LambdaQueryWrapper<JobApplication>()
                .eq(JobApplication::getStudentId, student.getId())
                .eq(JobApplication::getJobId, job.getId()));
        if (alreadyApplied > 0) {
            throw new BusinessException("已投递过该岗位，请勿重复投递");
        }

        body.setId(null);
        body.setStudentId(student.getId());
        body.setCompanyId(company.getId());
        body.setStatus("PENDING");
        body.setRemark(null);
        service.save(body);

        createNotification(
                company.getUserId(),
                "收到新的简历投递",
                "岗位【" + job.getJobName() + "】收到一份新的简历投递，请及时处理",
                "APPLICATION"
        );
        log.info("简历投递成功: applicationId={}, studentId={}, jobId={}, companyId={}",
                body.getId(), student.getId(), job.getId(), company.getId());
        return Result.success(body);
    }

    @GetMapping("/by-student")
    public Result<List<JobApplication>> listByStudent(@RequestParam(required = false) Long studentId) {
        Long scopedStudentId = resolveStudentId(studentId);
        return Result.success(service.list(new LambdaQueryWrapper<JobApplication>()
                .eq(JobApplication::getStudentId, scopedStudentId)
                .orderByDesc(JobApplication::getCreatedAt)));
    }

    @GetMapping("/by-student/detail")
    public Result<List<StudentApplicationDetail>> listStudentDetails() {
        Long studentId = findCurrentStudentProfileId();
        if (studentId == null) {
            return Result.success(List.of());
        }
        List<JobApplication> applications = service.list(new LambdaQueryWrapper<JobApplication>()
                .eq(JobApplication::getStudentId, studentId)
                .orderByDesc(JobApplication::getCreatedAt));
        return Result.success(applications.stream().map(this::toStudentDetail).toList());
    }

    @GetMapping("/by-company")
    public Result<List<JobApplication>> listByCompany(@RequestParam(required = false) Long companyId) {
        Long scopedCompanyId = resolveCompanyId(companyId);
        return Result.success(service.list(new LambdaQueryWrapper<JobApplication>()
                .eq(JobApplication::getCompanyId, scopedCompanyId)
                .orderByDesc(JobApplication::getCreatedAt)));
    }

    @GetMapping("/by-company/detail")
    public Result<List<CompanyApplicationDetail>> listCompanyDetails(@RequestParam(required = false) Long companyId) {
        Long scopedCompanyId = resolveCompanyId(companyId);
        List<JobApplication> applications = service.list(new LambdaQueryWrapper<JobApplication>()
                .eq(JobApplication::getCompanyId, scopedCompanyId)
                .orderByDesc(JobApplication::getCreatedAt));
        return Result.success(applications.stream().map(this::toCompanyDetail).toList());
    }

    @PatchMapping("/{id}/status")
    public Result<Void> updateStatus(
            @PathVariable Long id,
            @RequestParam String status,
            @RequestParam(required = false) String remark
    ) {
        return doUpdateStatus(id, status, remark);
    }

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
        CurrentUser currentUser = CurrentUserContext.require();
        if (!"STUDENT".equals(currentUser.getRole())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        JobApplication existing = service.getById(id);
        if (existing == null) {
            throw new BusinessException(ResultCode.NOT_FOUND);
        }
        Long studentId = currentStudentProfile().getId();
        if (!studentId.equals(existing.getStudentId())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        if (!"PENDING".equals(existing.getStatus())) {
            throw new BusinessException("只有待处理投递可以撤回");
        }
        service.removeById(id);
        log.info("学生撤回投递: applicationId={}, studentId={}, operator={}", id, studentId, currentUser.getUsername());
        return Result.success();
    }

    private Result<Void> doUpdateStatus(Long id, String status, String remark) {
        if (!"PENDING".equals(status) && !"PASSED".equals(status) && !"REJECTED".equals(status)) {
            throw new BusinessException("投递状态只能是 PENDING、PASSED 或 REJECTED");
        }
        JobApplication existing = service.getById(id);
        if (existing == null) {
            throw new BusinessException(ResultCode.NOT_FOUND);
        }
        CurrentUser currentUser = CurrentUserContext.require();
        if ("COMPANY".equals(currentUser.getRole())) {
            Long companyId = currentCompany().getId();
            if (!companyId.equals(existing.getCompanyId())) {
                throw new BusinessException(ResultCode.FORBIDDEN);
            }
        } else if (!"ADMIN".equals(currentUser.getRole())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }

        JobApplication application = new JobApplication();
        application.setId(id);
        application.setStatus(status);
        application.setRemark(remark);
        service.updateById(application);
        log.info("投递状态更新: applicationId={}, {} -> {}, operator={}",
                id, existing.getStatus(), status, currentUser.getUsername());
        notifyStudentApplicationStatus(existing, status, remark);
        return Result.success();
    }

    private LambdaQueryWrapper<JobApplication> scopedWrapper() {
        CurrentUser currentUser = CurrentUserContext.require();
        LambdaQueryWrapper<JobApplication> wrapper = new LambdaQueryWrapper<JobApplication>()
                .orderByDesc(JobApplication::getCreatedAt);
        if ("STUDENT".equals(currentUser.getRole())) {
            wrapper.eq(JobApplication::getStudentId, currentStudentProfile().getId());
        } else if ("COMPANY".equals(currentUser.getRole())) {
            wrapper.eq(JobApplication::getCompanyId, currentCompany().getId());
        }
        return wrapper;
    }

    private Long resolveStudentId(Long requestedStudentId) {
        CurrentUser currentUser = CurrentUserContext.require();
        if ("ADMIN".equals(currentUser.getRole())) {
            if (requestedStudentId == null) {
                throw new BusinessException("studentId 不能为空");
            }
            return requestedStudentId;
        }
        if (!"STUDENT".equals(currentUser.getRole())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        return currentStudentProfile().getId();
    }

    private Long resolveCompanyId(Long requestedCompanyId) {
        CurrentUser currentUser = CurrentUserContext.require();
        if ("ADMIN".equals(currentUser.getRole())) {
            if (requestedCompanyId == null) {
                throw new BusinessException("companyId 不能为空");
            }
            return requestedCompanyId;
        }
        if (!"COMPANY".equals(currentUser.getRole())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        return currentCompany().getId();
    }

    private StudentProfile currentStudentProfile() {
        StudentProfile profile = studentProfileService.getOne(new LambdaQueryWrapper<StudentProfile>()
                .eq(StudentProfile::getUserId, CurrentUserContext.userId())
                .last("limit 1"));
        if (profile == null) {
            throw new BusinessException("请先完善学生个人资料");
        }
        return profile;
    }

    private Long findCurrentStudentProfileId() {
        CurrentUser currentUser = CurrentUserContext.require();
        if (!"STUDENT".equals(currentUser.getRole())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        StudentProfile profile = studentProfileService.getOne(new LambdaQueryWrapper<StudentProfile>()
                .eq(StudentProfile::getUserId, currentUser.getUserId())
                .last("limit 1"));
        return profile == null ? null : profile.getId();
    }

    private Company currentCompany() {
        Company company = companyService.getOne(new LambdaQueryWrapper<Company>()
                .eq(Company::getUserId, CurrentUserContext.userId())
                .last("limit 1"));
        if (company == null) {
            throw new BusinessException("请先完善企业信息");
        }
        return company;
    }

    private CompanyApplicationDetail toCompanyDetail(JobApplication application) {
        CompanyApplicationDetail detail = new CompanyApplicationDetail();
        detail.setId(application.getId());
        detail.setJobId(application.getJobId());
        detail.setCompanyId(application.getCompanyId());
        detail.setStudentId(application.getStudentId());
        detail.setResumeId(application.getResumeId());
        detail.setStatus(application.getStatus());
        detail.setRemark(application.getRemark());
        detail.setCreatedAt(application.getCreatedAt());
        detail.setUpdatedAt(application.getUpdatedAt());

        Job job = jobService.getById(application.getJobId());
        if (job != null) {
            detail.setJobName(job.getJobName());
            detail.setJobType(job.getJobType());
            detail.setCity(job.getCity());
            detail.setSalaryRange(job.getSalaryRange());
        }
        StudentProfile student = studentProfileService.getById(application.getStudentId());
        if (student != null) {
            detail.setStudentName(student.getRealName());
            detail.setSchool(student.getSchool());
            detail.setMajor(student.getMajor());
            detail.setEducationLevel(student.getEducationLevel());
            detail.setPhone(student.getPhone());
            detail.setEmail(student.getEmail());
            detail.setGender(student.getGender());
        }
        Resume resume = resumeService.getById(application.getResumeId());
        if (resume != null) {
            detail.setResumeName(resume.getResumeName());
            detail.setResumeType(resume.getResumeType());
            detail.setTargetPosition(resume.getTargetPosition());
            detail.setResumeFileId(resume.getFileId());
        }
        return detail;
    }

    private StudentApplicationDetail toStudentDetail(JobApplication application) {
        StudentApplicationDetail detail = new StudentApplicationDetail();
        detail.setId(application.getId());
        detail.setJobId(application.getJobId());
        detail.setCompanyId(application.getCompanyId());
        detail.setStudentId(application.getStudentId());
        detail.setResumeId(application.getResumeId());
        detail.setStatus(application.getStatus());
        detail.setRemark(application.getRemark());
        detail.setCreatedAt(application.getCreatedAt());
        detail.setUpdatedAt(application.getUpdatedAt());

        Job job = jobService.getById(application.getJobId());
        if (job != null) {
            detail.setJobName(job.getJobName());
            detail.setJobType(job.getJobType());
            detail.setCity(job.getCity());
            detail.setSalaryRange(job.getSalaryRange());
        }
        Company company = companyService.getById(application.getCompanyId());
        if (company != null) {
            detail.setCompanyName(company.getCompanyName());
        }
        Resume resume = resumeService.getById(application.getResumeId());
        if (resume != null) {
            detail.setResumeName(resume.getResumeName());
            detail.setResumeType(resume.getResumeType());
            detail.setTargetPosition(resume.getTargetPosition());
            detail.setResumeFileId(resume.getFileId());
        }
        return detail;
    }

    private void notifyStudentApplicationStatus(JobApplication application, String status, String remark) {
        StudentProfile student = studentProfileService.getById(application.getStudentId());
        if (student == null || student.getUserId() == null) {
            return;
        }
        Job job = jobService.getById(application.getJobId());
        String jobName = job == null ? "已投递岗位" : job.getJobName();
        String content = "你的岗位【" + jobName + "】投递状态已更新为 " + status;
        if (remark != null && !remark.isBlank()) {
            content += "，备注：" + remark;
        }
        createNotification(student.getUserId(), "投递状态更新", content, "APPLICATION");
    }

    private void createNotification(Long receiverId, String title, String content, String type) {
        if (receiverId == null) {
            return;
        }
        Notification notification = new Notification();
        notification.setReceiverId(receiverId);
        notification.setTitle(title);
        notification.setContent(content);
        notification.setType(type);
        notification.setIsRead(0);
        notificationService.save(notification);
    }
}
