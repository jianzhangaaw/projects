package com.recruit_resume.controller;

import com.recruit_resume.common.BusinessException;
import com.recruit_resume.dto.StudentApplicationDetail;
import com.recruit_resume.security.CurrentUser;
import com.recruit_resume.security.CurrentUserContext;
import com.recruit_resume.service.JobApplicationService;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * Controller 在阶段二之后只做参数解析与角色门禁，装配、状态机、事务都在 Service 里。
 * 这里验证的是「有没有把当前用户正确传下去」和「角色不对时有没有挡住」。
 * 业务规则的验证见 scripts/check-consistency.py（集成测试）。
 */
class JobApplicationControllerTest {

    private final JobApplicationService service = mock(JobApplicationService.class);
    private final JobApplicationController controller = new JobApplicationController(service);

    @AfterEach
    void clearCurrentUser() {
        CurrentUserContext.clear();
    }

    @Test
    void listStudentDetailsPassesCurrentUserIdToService() {
        CurrentUserContext.set(new CurrentUser(7L, "student", "STUDENT"));
        StudentApplicationDetail detail = new StudentApplicationDetail();
        detail.setId(3L);
        detail.setJobName("后端开发工程师");
        when(service.listStudentDetails(7L)).thenReturn(List.of(detail));

        var rows = controller.listStudentDetails().getData();

        assertEquals(1, rows.size());
        assertEquals("后端开发工程师", rows.get(0).getJobName());
        verify(service).listStudentDetails(7L);
    }

    @Test
    void withdrawRejectsNonStudent() {
        CurrentUserContext.set(new CurrentUser(9L, "hr", "COMPANY"));

        BusinessException exception = assertThrows(BusinessException.class, () -> controller.withdraw(3L));

        assertEquals(403, exception.getCode());
    }

    @Test
    void createRejectsNonStudent() {
        CurrentUserContext.set(new CurrentUser(9L, "hr", "COMPANY"));
        com.recruit_resume.entity.JobApplication body = new com.recruit_resume.entity.JobApplication();
        body.setJobId(1L);

        BusinessException exception = assertThrows(BusinessException.class, () -> controller.create(body));

        assertEquals(403, exception.getCode());
    }

    @Test
    void updateStatusDelegatesRoleAndUserToService() {
        CurrentUserContext.set(new CurrentUser(9L, "hr", "COMPANY"));

        controller.updateStatus(3L, "PASSED", "不错");

        verify(service).updateStatus(9L, "COMPANY", 3L, "PASSED", "不错");
    }
}
