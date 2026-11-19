package com.recruit_resume.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.recruit_resume.common.BusinessException;
import com.recruit_resume.common.ResultCode;
import com.recruit_resume.dto.CompanyApplicationDetail;
import com.recruit_resume.dto.StudentApplicationDetail;
import com.recruit_resume.entity.Company;
import com.recruit_resume.entity.Job;
import com.recruit_resume.entity.JobApplication;
import com.recruit_resume.entity.Notification;
import com.recruit_resume.entity.Resume;
import com.recruit_resume.entity.StudentProfile;
import com.recruit_resume.mapper.JobApplicationMapper;
import com.recruit_resume.service.CompanyService;
import com.recruit_resume.service.JobApplicationService;
import com.recruit_resume.service.JobService;
import com.recruit_resume.service.NotificationService;
import com.recruit_resume.service.ResumeService;
import com.recruit_resume.service.StudentProfileService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

@Slf4j
@Service
public class JobApplicationServiceImpl extends ServiceImpl<JobApplicationMapper, JobApplication>
        implements JobApplicationService {

    /** 投递状态机：只有 PENDING 可以流转，且只能到 PASSED / REJECTED。 */
    private static final Map<String, List<String>> STATUS_TRANSITIONS = Map.of(
            "PENDING", List.of("PASSED", "REJECTED"),
            "PASSED", List.of(),
            "REJECTED", List.of()
    );

    private static final String STATUS_PENDING = "PENDING";

    private final JobService jobService;
    private final CompanyService companyService;
    private final StudentProfileService studentProfileService;
    private final ResumeService resumeService;
    private final NotificationService notificationService;

    public JobApplicationServiceImpl(
            JobService jobService,
            CompanyService companyService,
            StudentProfileService studentProfileService,
            ResumeService resumeService,
            NotificationService notificationService
    ) {
        this.jobService = jobService;
        this.companyService = companyService;
        this.studentProfileService = studentProfileService;
        this.resumeService = resumeService;
        this.notificationService = notificationService;
    }

    // ------------------------------------------------------------------ 写

    @Override
    @Transactional
    public JobApplication apply(Long userId, Long jobId, Long resumeId) {
        StudentProfile student = requireStudentProfile(userId);
        Job job = jobService.getById(jobId);
        if (job == null || !"PUBLISHED".equals(job.getStatus())) {
            throw new BusinessException("岗位不存在或未发布");
        }
        Company company = companyService.getById(job.getCompanyId());
        if (company == null) {
            throw new BusinessException("岗位所属企业不存在");
        }
        if (resumeId != null) {
            Resume resume = resumeService.getById(resumeId);
            if (resume == null) {
                throw new BusinessException("所选简历不存在");
            }
            if (!student.getId().equals(resume.getStudentId())) {
                throw new BusinessException(ResultCode.FORBIDDEN.getCode(), "只能投递自己的简历");
            }
        }

        JobApplication application = new JobApplication();
        application.setJobId(job.getId());
        application.setCompanyId(company.getId());
        application.setStudentId(student.getId());
        application.setResumeId(resumeId);
        application.setStatus(STATUS_PENDING);

        try {
            save(application);
        } catch (DuplicateKeyException ex) {
            // 表上有 uk_job_application_job_student，并发投递时由数据库兜底。
            // 早期只做了「先 count 再 insert」，两个并发请求都能通过检查然后插两条（或第二条 500）。
            log.warn("重复投递被唯一索引拦下: studentId={}, jobId={}", student.getId(), jobId);
            throw new BusinessException("已投递过该岗位，请勿重复投递");
        }

        // 通知和投递在同一个事务里：通知写失败就整体回滚，不会出现「投了但企业收不到」
        notifyApplication(company.getUserId(), job.getJobName(), "收到新的简历投递",
                "岗位【" + job.getJobName() + "】收到一份新的简历投递，请及时处理");
        log.info("简历投递成功: applicationId={}, studentId={}, jobId={}, companyId={}",
                application.getId(), student.getId(), job.getId(), company.getId());
        return application;
    }

    @Override
    @Transactional
    public void withdraw(Long userId, Long applicationId) {
        StudentProfile student = requireStudentProfile(userId);
        JobApplication existing = getById(applicationId);
        if (existing == null) {
            throw new BusinessException(ResultCode.NOT_FOUND);
        }
        if (!student.getId().equals(existing.getStudentId())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        if (!STATUS_PENDING.equals(existing.getStatus())) {
            throw new BusinessException("只有待处理的投递可以撤回");
        }
        removeById(applicationId);
        log.info("学生撤回投递: applicationId={}, studentId={}", applicationId, student.getId());
    }

    @Override
    @Transactional
    public void updateStatus(Long userId, String role, Long applicationId, String status, String remark) {
        if (!STATUS_TRANSITIONS.containsKey(status)) {
            throw new BusinessException("投递状态只能是 PENDING、PASSED 或 REJECTED");
        }
        JobApplication existing = getById(applicationId);
        if (existing == null) {
            throw new BusinessException(ResultCode.NOT_FOUND);
        }

        // 企业只能改自己收到的那条
        if ("COMPANY".equals(role)) {
            Company company = requireCompany(userId);
            if (!company.getId().equals(existing.getCompanyId())) {
                throw new BusinessException(ResultCode.FORBIDDEN);
            }
        } else if (!"ADMIN".equals(role)) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }

        List<String> allowed = STATUS_TRANSITIONS.getOrDefault(existing.getStatus(), List.of());
        if (!allowed.contains(status)) {
            throw new BusinessException("投递状态不能从 " + existing.getStatus() + " 改为 " + status);
        }

        JobApplication update = new JobApplication();
        update.setId(applicationId);
        update.setStatus(status);
        update.setRemark(remark);
        updateById(update);

        Job job = jobService.getById(existing.getJobId());
        String jobName = job == null ? "已投递岗位" : job.getJobName();
        String content = "你的岗位【" + jobName + "】投递状态已更新为 " + status;
        if (remark != null && !remark.isBlank()) {
            content += "，备注：" + remark;
        }
        StudentProfile student = studentProfileService.getById(existing.getStudentId());
        if (student != null && student.getUserId() != null) {
            notifyApplication(student.getUserId(), jobName, "投递状态更新", content);
        }
        log.info("投递状态更新: applicationId={}, {} -> {}, operator(userId={},role={})",
                applicationId, existing.getStatus(), status, userId, role);
    }

    // ------------------------------------------------------------------ 读

    @Override
    public IPage<JobApplication> pageForUser(Long userId, String role, long current, long size) {
        LambdaQueryWrapper<JobApplication> wrapper = new LambdaQueryWrapper<JobApplication>()
                .orderByDesc(JobApplication::getCreatedAt);
        if ("STUDENT".equals(role)) {
            wrapper.eq(JobApplication::getStudentId, requireStudentProfile(userId).getId());
        } else if ("COMPANY".equals(role)) {
            wrapper.eq(JobApplication::getCompanyId, requireCompany(userId).getId());
        }
        return page(Page.of(current, size), wrapper);
    }

    @Override
    public List<JobApplication> listByStudent(Long userId) {
        Long studentId = requireStudentProfile(userId).getId();
        return list(new LambdaQueryWrapper<JobApplication>()
                .eq(JobApplication::getStudentId, studentId)
                .orderByDesc(JobApplication::getCreatedAt));
    }

    @Override
    public List<JobApplication> listByCompany(Long userId) {
        Long companyId = requireCompany(userId).getId();
        return list(new LambdaQueryWrapper<JobApplication>()
                .eq(JobApplication::getCompanyId, companyId)
                .orderByDesc(JobApplication::getCreatedAt));
    }

    @Override
    public List<StudentApplicationDetail> listStudentDetails(Long userId) {
        List<JobApplication> applications = listByStudent(userId);
        if (applications.isEmpty()) {
            return List.of();
        }
        // 批量装配：原来每条投递要查 job / company / resume 三次，100 条就是 300 次查询
        Map<Long, Job> jobs = byIds(applications.stream().map(JobApplication::getJobId), jobService::listByIds, Job::getId);
        Map<Long, Company> companies = byIds(applications.stream().map(JobApplication::getCompanyId), companyService::listByIds, Company::getId);
        Map<Long, Resume> resumes = byIds(applications.stream().map(JobApplication::getResumeId), resumeService::listByIds, Resume::getId);

        List<StudentApplicationDetail> result = new ArrayList<>(applications.size());
        for (JobApplication app : applications) {
            StudentApplicationDetail d = new StudentApplicationDetail();
            d.setId(app.getId());
            d.setJobId(app.getJobId());
            d.setCompanyId(app.getCompanyId());
            d.setStudentId(app.getStudentId());
            d.setResumeId(app.getResumeId());
            d.setStatus(app.getStatus());
            d.setRemark(app.getRemark());
            d.setCreatedAt(app.getCreatedAt());
            d.setUpdatedAt(app.getUpdatedAt());

            Job job = jobs.get(app.getJobId());
            if (job != null) {
                d.setJobName(job.getJobName());
                d.setJobType(job.getJobType());
                d.setCity(job.getCity());
                d.setSalaryRange(job.getSalaryRange());
            }
            Company company = companies.get(app.getCompanyId());
            if (company != null) {
                d.setCompanyName(company.getCompanyName());
            }
            Resume resume = resumes.get(app.getResumeId());
            if (resume != null) {
                d.setResumeName(resume.getResumeName());
                d.setResumeType(resume.getResumeType());
                d.setTargetPosition(resume.getTargetPosition());
                d.setResumeFileId(resume.getFileId());
            }
            result.add(d);
        }
        return result;
    }

    @Override
    public List<CompanyApplicationDetail> listCompanyDetails(Long userId) {
        List<JobApplication> applications = listByCompany(userId);
        if (applications.isEmpty()) {
            return List.of();
        }
        Map<Long, Job> jobs = byIds(applications.stream().map(JobApplication::getJobId), jobService::listByIds, Job::getId);
        Map<Long, StudentProfile> students = byIds(applications.stream().map(JobApplication::getStudentId), studentProfileService::listByIds, StudentProfile::getId);
        Map<Long, Resume> resumes = byIds(applications.stream().map(JobApplication::getResumeId), resumeService::listByIds, Resume::getId);

        List<CompanyApplicationDetail> result = new ArrayList<>(applications.size());
        for (JobApplication app : applications) {
            CompanyApplicationDetail d = new CompanyApplicationDetail();
            d.setId(app.getId());
            d.setJobId(app.getJobId());
            d.setCompanyId(app.getCompanyId());
            d.setStudentId(app.getStudentId());
            d.setResumeId(app.getResumeId());
            d.setStatus(app.getStatus());
            d.setRemark(app.getRemark());
            d.setCreatedAt(app.getCreatedAt());
            d.setUpdatedAt(app.getUpdatedAt());

            Job job = jobs.get(app.getJobId());
            if (job != null) {
                d.setJobName(job.getJobName());
                d.setJobType(job.getJobType());
                d.setCity(job.getCity());
                d.setSalaryRange(job.getSalaryRange());
            }
            StudentProfile student = students.get(app.getStudentId());
            if (student != null) {
                d.setStudentName(student.getRealName());
                d.setSchool(student.getSchool());
                d.setMajor(student.getMajor());
                d.setEducationLevel(student.getEducationLevel());
                d.setPhone(student.getPhone());
                d.setEmail(student.getEmail());
                d.setGender(student.getGender());
            }
            Resume resume = resumes.get(app.getResumeId());
            if (resume != null) {
                d.setResumeName(resume.getResumeName());
                d.setResumeType(resume.getResumeType());
                d.setTargetPosition(resume.getTargetPosition());
                d.setResumeFileId(resume.getFileId());
            }
            result.add(d);
        }
        return result;
    }

    // ------------------------------------------------------------------ 辅助

    private <E> Map<Long, E> byIds(java.util.stream.Stream<Long> ids,
                                   Function<List<Long>, List<E>> loader,
                                   Function<E, Long> keyFn) {
        List<Long> distinct = ids.filter(java.util.Objects::nonNull).distinct().toList();
        if (distinct.isEmpty()) {
            return Map.of();
        }
        return loader.apply(distinct).stream()
                .collect(Collectors.toMap(keyFn, Function.identity(), (a, b) -> a));
    }

    private StudentProfile requireStudentProfile(Long userId) {
        StudentProfile profile = studentProfileService.getOne(new LambdaQueryWrapper<StudentProfile>()
                .eq(StudentProfile::getUserId, userId)
                .last("limit 1"));
        if (profile == null) {
            throw new BusinessException("请先完善学生个人资料");
        }
        return profile;
    }

    private Company requireCompany(Long userId) {
        Company company = companyService.getOne(new LambdaQueryWrapper<Company>()
                .eq(Company::getUserId, userId)
                .last("limit 1"));
        if (company == null) {
            throw new BusinessException("请先完善企业信息");
        }
        return company;
    }

    private void notifyApplication(Long receiverId, String jobName, String title, String content) {
        if (receiverId == null) {
            return;
        }
        Notification n = new Notification();
        n.setReceiverId(receiverId);
        n.setTitle(title);
        n.setContent(content);
        n.setType("APPLICATION");
        n.setIsRead(0);
        notificationService.save(n);
    }
}
