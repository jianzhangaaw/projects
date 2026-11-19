package com.recruit_resume.controller;

import com.recruit_resume.entity.StudentProfile;
import com.recruit_resume.entity.UserAccount;
import com.recruit_resume.security.CurrentUser;
import com.recruit_resume.security.CurrentUserContext;
import com.recruit_resume.service.StudentProfileService;
import com.recruit_resume.service.UserAccountService;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class StudentProfileControllerTest {

    @AfterEach
    void clearCurrentUser() {
        CurrentUserContext.clear();
    }

    @Test
    void getMyProfileFallsBackToAccountContactWhenProfileIsEmpty() {
        StudentProfileService profileService = mock(StudentProfileService.class);
        UserAccountService userAccountService = mock(UserAccountService.class);
        when(profileService.getOne(any())).thenReturn(null);

        UserAccount account = new UserAccount();
        account.setId(7L);
        account.setEmail("student@example.com");
        account.setPhone("13800000000");
        when(userAccountService.getById(7L)).thenReturn(account);

        CurrentUserContext.set(new CurrentUser(7L, "student", "STUDENT"));
        StudentProfileController controller = new StudentProfileController(profileService, userAccountService);

        StudentProfile profile = controller.getMyProfile().getData();

        assertEquals(7L, profile.getUserId());
        assertEquals("student@example.com", profile.getEmail());
        assertEquals("13800000000", profile.getPhone());
    }
}
