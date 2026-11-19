package com.recruit_resume.controller;

import com.recruit_resume.common.BusinessException;
import com.recruit_resume.entity.Company;
import com.recruit_resume.security.CurrentUser;
import com.recruit_resume.security.CurrentUserContext;
import com.recruit_resume.service.CompanyDraftService;
import com.recruit_resume.service.CompanyService;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class CompanyControllerTest {

    @AfterEach
    void clearCurrentUser() {
        CurrentUserContext.clear();
    }

    @Test
    void updateLogoRequiresExistingCompanyProfile() {
        // updateLogo 现在从 CurrentUserContext 取 userId（参数只做兼容校验），
        // 所以测试要先注入登录上下文，否则会先抛 401。
        CurrentUserContext.set(new CurrentUser(32L, "hr", "COMPANY"));
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

    @Test
    void updateLogoRejectsAnotherUsersId() {
        CurrentUserContext.set(new CurrentUser(32L, "hr", "COMPANY"));
        CompanyService companyService = mock(CompanyService.class);
        CompanyDraftService draftService = mock(CompanyDraftService.class);
        CompanyController controller = new CompanyController(companyService, draftService);

        BusinessException exception = assertThrows(
                BusinessException.class,
                () -> controller.updateLogo(99L, 12L)
        );

        assertEquals(403, exception.getCode());
    }
}
