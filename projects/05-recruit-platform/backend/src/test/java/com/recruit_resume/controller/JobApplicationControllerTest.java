package com.recruit_resume.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.recruit_resume.common.BusinessException;
import com.recruit_resume.entity.Company;
import com.recruit_resume.entity.Job;
import com.recruit_resume.entity.JobApplication;
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
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class JobApplicationControllerTest {

    private final JobApplicationService applicationService = mock(JobApplicationService.class);
    private final JobService jobService = mock(JobService.class);
    private final CompanyService companyService = mock(CompanyService.class);
    private final StudentProfileService studentProfileService = mock(StudentProfileService.class);
    private final ResumeService resumeService = mock(ResumeService.class);
    private final NotificationService notificationService = mock(NotificationService.class);
    private final JobApplicationController controller = new JobApplicationController(
            applicationService,
            jobService,
            companyService,
            studentProfileService,
            resumeService,
            notificationService
    );

    @AfterEach
    void clearCurrentUser() {
        CurrentUserContext.clear();
    }

    @Test
    void listStudentDetailsUsesCurrentStudentAndEnrichesRows() {
        CurrentUserContext.set(new CurrentUser(7L, "student", "STUDENT"));
        StudentProfile profile = new StudentProfile();
        profile.setId(20L);
        profile.setUserId(7L);
        when(studentProfileService.getOne(any(LambdaQueryWrapper.class))).thenReturn(profile);

        JobApplication application = new JobApplication();
        application.setId(3L);
        application.setStudentId(20L);
        application.setJobId(11L);
        application.setCompanyId(12L);
        application.setResumeId(13L);
        application.setStatus("PENDING");
        when(applicationService.list(any(LambdaQueryWrapper.class))).thenReturn(List.of(application));

        Job job = new Job();
        job.setId(11L);
        job.setCompanyId(12L);
        job.setJobName("后端开发工程师");
        job.setCity("杭州");
        job.setSalaryRange("15K-20K");
        when(jobService.getById(11L)).thenReturn(job);

        Company company = new Company();
        company.setId(12L);
        company.setCompanyName("星辰科技");
        when(companyService.getById(12L)).thenReturn(company);

        Resume resume = new Resume();
        resume.setId(13L);
        resume.setResumeName("后端开发简历");
        resume.setFileId(99L);
        when(resumeService.getById(13L)).thenReturn(resume);

        var rows = controller.listStudentDetails().getData();

        assertEquals(1, rows.size());
        assertEquals("后端开发工程师", rows.get(0).getJobName());
        assertEquals("星辰科技", rows.get(0).getCompanyName());
        assertEquals("后端开发简历", rows.get(0).getResumeName());
        assertEquals(99L, rows.get(0).getResumeFileId());
    }

    @Test
    void listStudentDetailsReturnsEmptyWhenProfileNotCreated() {
        CurrentUserContext.set(new CurrentUser(7L, "student", "STUDENT"));
        when(studentProfileService.getOne(any(LambdaQueryWrapper.class))).thenReturn(null);

        var rows = controller.listStudentDetails().getData();

        assertEquals(0, rows.size());
        verify(applicationService, never()).list(any(LambdaQueryWrapper.class));
    }

    @Test
    void withdrawOnlyAllowsCurrentStudentPendingApplication() {
        CurrentUserContext.set(new CurrentUser(7L, "student", "STUDENT"));
        StudentProfile profile = new StudentProfile();
        profile.setId(20L);
        profile.setUserId(7L);
        when(studentProfileService.getOne(any(LambdaQueryWrapper.class))).thenReturn(profile);

        JobApplication application = new JobApplication();
        application.setId(3L);
        application.setStudentId(20L);
        application.setStatus("PENDING");
        when(applicationService.getById(3L)).thenReturn(application);

        controller.withdraw(3L);

        verify(applicationService).removeById(3L);
    }

    @Test
    void withdrawRejectsProcessedApplication() {
        CurrentUserContext.set(new CurrentUser(7L, "student", "STUDENT"));
        StudentProfile profile = new StudentProfile();
        profile.setId(20L);
        profile.setUserId(7L);
        when(studentProfileService.getOne(any(LambdaQueryWrapper.class))).thenReturn(profile);

        JobApplication application = new JobApplication();
        application.setId(3L);
        application.setStudentId(20L);
        application.setStatus("PASSED");
        when(applicationService.getById(3L)).thenReturn(application);

        BusinessException exception = assertThrows(BusinessException.class, () -> controller.withdraw(3L));

        assertEquals("只有待处理投递可以撤回", exception.getMessage());
        verify(applicationService, never()).removeById(3L);
    }
}
