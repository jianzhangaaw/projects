package com.recruit_resume.service;

import com.recruit_resume.common.BusinessException;
import com.recruit_resume.dto.RegisterRequest;
import com.recruit_resume.entity.StudentProfile;
import com.recruit_resume.entity.UserAccount;
import com.recruit_resume.security.JwtTokenProvider;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class AuthServiceTest {

    @Test
    void registerStoresBlankEmailAndPhoneAsNull() {
        UserAccountService userAccountService = mock(UserAccountService.class);
        StudentProfileService studentProfileService = mock(StudentProfileService.class);
        JwtTokenProvider jwtTokenProvider = mock(JwtTokenProvider.class);
        when(userAccountService.save(any(UserAccount.class))).thenReturn(true);
        AuthService authService = new AuthService(userAccountService, studentProfileService, jwtTokenProvider);

        RegisterRequest request = new RegisterRequest();
        request.setUsername("blank-contact-user");
        request.setPassword("123456");
        request.setRole("STUDENT");
        request.setEmail(" ");
        request.setPhone("");

        UserAccount registered = authService.register(request);

        ArgumentCaptor<UserAccount> captor = ArgumentCaptor.forClass(UserAccount.class);
        verify(userAccountService).save(captor.capture());
        UserAccount saved = captor.getValue();
        assertNull(saved.getEmail());
        assertNull(saved.getPhone());
        assertNull(registered.getPassword());
    }

    @Test
    void registerCreatesStudentProfileWithAccountContact() {
        UserAccountService userAccountService = mock(UserAccountService.class);
        StudentProfileService studentProfileService = mock(StudentProfileService.class);
        JwtTokenProvider jwtTokenProvider = mock(JwtTokenProvider.class);
        when(userAccountService.save(any(UserAccount.class))).thenAnswer(invocation -> {
            UserAccount account = invocation.getArgument(0);
            account.setId(88L);
            return true;
        });
        AuthService authService = new AuthService(userAccountService, studentProfileService, jwtTokenProvider);

        RegisterRequest request = new RegisterRequest();
        request.setUsername("student-contact-user");
        request.setPassword("123456");
        request.setRole("STUDENT");
        request.setEmail("student@example.com");
        request.setPhone("13800000000");

        authService.register(request);

        ArgumentCaptor<StudentProfile> captor = ArgumentCaptor.forClass(StudentProfile.class);
        verify(studentProfileService).save(captor.capture());
        StudentProfile profile = captor.getValue();
        assertEquals(88L, profile.getUserId());
        assertEquals("student@example.com", profile.getEmail());
        assertEquals("13800000000", profile.getPhone());
    }

    @Test
    void registerRejectsAdminRoleToPreventPrivilegeEscalation() {
        UserAccountService userAccountService = mock(UserAccountService.class);
        StudentProfileService studentProfileService = mock(StudentProfileService.class);
        JwtTokenProvider jwtTokenProvider = mock(JwtTokenProvider.class);
        AuthService authService = new AuthService(userAccountService, studentProfileService, jwtTokenProvider);

        RegisterRequest request = new RegisterRequest();
        request.setUsername("admin-user");
        request.setPassword("123456");
        request.setRole("ADMIN");

        BusinessException exception = assertThrows(
                BusinessException.class,
                () -> authService.register(request)
        );

        assertEquals("角色不合法，仅支持 STUDENT / COMPANY", exception.getMessage());
        verify(userAccountService, never()).save(any(UserAccount.class));
    }

    @Test
    void registerRejectsInvalidRole() {
        UserAccountService userAccountService = mock(UserAccountService.class);
        StudentProfileService studentProfileService = mock(StudentProfileService.class);
        JwtTokenProvider jwtTokenProvider = mock(JwtTokenProvider.class);
        AuthService authService = new AuthService(userAccountService, studentProfileService, jwtTokenProvider);

        RegisterRequest request = new RegisterRequest();
        request.setUsername("hacker");
        request.setPassword("123456");
        request.setRole("SUPER_ADMIN");

        BusinessException exception = assertThrows(
                BusinessException.class,
                () -> authService.register(request)
        );

        assertEquals("角色不合法，仅支持 STUDENT / COMPANY", exception.getMessage());
        verify(userAccountService, never()).save(any(UserAccount.class));
    }
}
