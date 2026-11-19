package com.recruit_resume.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.recruit_resume.common.PageQuery;
import com.recruit_resume.entity.Company;
import com.recruit_resume.entity.Job;
import com.recruit_resume.service.CompanyService;
import com.recruit_resume.service.JobService;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.argThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class JobControllerTest {

    @Test
    void publishedEnrichesJobsWithOneBatchCompanyLookup() {
        JobService jobService = mock(JobService.class);
        CompanyService companyService = mock(CompanyService.class);
        JobController controller = new JobController(jobService, companyService);

        Job first = job(1L, 7L);
        Job second = job(2L, 7L);
        Job third = job(3L, 9L);
        Page<Job> page = Page.of(1, 12);
        page.setRecords(List.of(first, second, third));
        when(jobService.page(any(Page.class), any())).thenReturn(page);

        Company firstCompany = company(7L, "星海科技", "互联网", "100-499人");
        Company secondCompany = company(9L, "远山智造", "智能制造", "500-999人");
        when(companyService.listByIds(any())).thenReturn(List.of(firstCompany, secondCompany));

        IPage<Job> result = assertDoesNotThrow(
                () -> controller.published(new PageQuery(), null, null, null)
        ).getData();

        assertEquals("星海科技", result.getRecords().get(0).getCompanyName());
        assertEquals("互联网", result.getRecords().get(1).getIndustry());
        assertEquals("500-999人", result.getRecords().get(2).getCompanySize());
        verify(companyService).listByIds(argThat(ids -> ids.size() == 2 && ids.containsAll(List.of(7L, 9L))));
        verify(companyService, never()).getById(any());
    }

    @Test
    void publishedDoesNotQueryCompaniesForAnEmptyPage() {
        JobService jobService = mock(JobService.class);
        CompanyService companyService = mock(CompanyService.class);
        JobController controller = new JobController(jobService, companyService);
        Page<Job> page = Page.of(1, 12);
        page.setRecords(List.of());
        when(jobService.page(any(Page.class), any())).thenReturn(page);

        IPage<Job> result = controller.published(new PageQuery(), null, null, null).getData();

        assertEquals(0, result.getRecords().size());
        verify(companyService, never()).listByIds(any());
    }

    @Test
    void publishedKeepsJobWhenItsCompanyRecordIsMissing() {
        JobService jobService = mock(JobService.class);
        CompanyService companyService = mock(CompanyService.class);
        JobController controller = new JobController(jobService, companyService);
        Job job = job(5L, 99L);
        Page<Job> page = Page.of(1, 12);
        page.setRecords(List.of(job));
        when(jobService.page(any(Page.class), any())).thenReturn(page);
        when(companyService.listByIds(any())).thenReturn(List.of());

        IPage<Job> result = assertDoesNotThrow(
                () -> controller.published(new PageQuery(), null, null, null)
        ).getData();

        assertEquals(1, result.getRecords().size());
        assertNull(result.getRecords().get(0).getCompanyName());
    }

    private Job job(Long id, Long companyId) {
        Job job = new Job();
        job.setId(id);
        job.setCompanyId(companyId);
        return job;
    }

    private Company company(Long id, String name, String industry, String size) {
        Company company = new Company();
        company.setId(id);
        company.setCompanyName(name);
        company.setIndustry(industry);
        company.setCompanySize(size);
        return company;
    }
}
