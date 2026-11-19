package com.recruit_resume.controller;

import com.recruit_resume.common.BusinessException;
import com.recruit_resume.entity.Company;
import com.recruit_resume.service.CompanyDraftService;
import com.recruit_resume.service.CompanyService;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class CompanyControllerTest {

    @Test
    void updateLogoRequiresExistingCompanyProfile() {
        CompanyService companyService = mock(CompanyService.class);
        CompanyDraftService draftService = mock(CompanyDraftService.class);
        when(companyService.getOne(any())).thenReturn(null);
        CompanyController controller = new CompanyController(companyService, draftService);

        BusinessException exception = assertThrows(
                BusinessException.class,
                () -> controller.updateLogo(32L, 12L)
        );

        assertEquals(400, exception.getCode());
        assertEquals("请先保存企业基本信息", exception.getMessage());
        verify(companyService, never()).save(any(Company.class));
    }
}