package com.recruit_resume.service;

import com.recruit_resume.common.BusinessException;
import com.recruit_resume.common.RequestCache;
import com.recruit_resume.entity.StudentProfile;
import com.recruit_resume.entity.UserAccount;
import com.recruit_resume.security.CurrentUser;
import com.recruit_resume.security.CurrentUserContext;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * 请求级缓存的回归测试。
 *
 * <p>两件事必须同时成立：同一请求内只查一次库；请求结束清理后必须重新查库
 * （否则线程池复用线程会把上一个请求的学生资料带给下一个请求，是数据泄漏级别的 bug）。
 */
class StudentProfileResolverTest {

    @AfterEach
    void clearCaches() {
        RequestCache.clear();
        CurrentUserContext.clear();
    }

    @Test
    void sameRequestHitsDatabaseOnceAndClearedRequestQueriesAgain() {
        StudentProfileService profileService = mock(StudentProfileService.class);
        UserAccountService accountService = mock(UserAccountService.class);
        StudentProfile profile = new StudentProfile();
        profile.setId(3L);
        profile.setUserId(7L);
        when(profileService.getOne(any())).thenReturn(profile);

        CurrentUserContext.set(new CurrentUser(7L, "student07", "STUDENT"));
        StudentProfileResolver resolver = new StudentProfileResolver(profileService, accountService);

        StudentProfile first = resolver.getOrCreateCurrentStudentProfile();
        StudentProfile second = resolver.getOrCreateCurrentStudentProfile();

        assertSame(first, second);
        verify(profileService, times(1)).getOne(any());

        RequestCache.clear();
        resolver.getOrCreateCurrentStudentProfile();
        verify(profileService, times(2)).getOne(any());
    }

    @Test
    void createsMissingProfileAndCachesIt() {
        StudentProfileService profileService = mock(StudentProfileService.class);
        UserAccountService accountService = mock(UserAccountService.class);
        when(profileService.getOne(any())).thenReturn(null);
        when(accountService.getById(7L)).thenReturn(new UserAccount());
        when(profileService.save(any(StudentProfile.class))).thenReturn(true);

        CurrentUserContext.set(new CurrentUser(7L, "student07", "STUDENT"));
        StudentProfileResolver resolver = new StudentProfileResolver(profileService, accountService);

        StudentProfile created = resolver.getOrCreateCurrentStudentProfile();
        assertEquals(7L, created.getUserId().longValue());
        verify(profileService).save(any(StudentProfile.class));

        // 建完之后再取一次不应该再查库，也不应该再建一条
        resolver.getOrCreateCurrentStudentProfile();
        verify(profileService, times(1)).getOne(any());
        verify(profileService, times(1)).save(any(StudentProfile.class));
    }

    @Test
    void rejectsNonStudentRole() {
        StudentProfileService profileService = mock(StudentProfileService.class);
        UserAccountService accountService = mock(UserAccountService.class);
        CurrentUserContext.set(new CurrentUser(9L, "company09", "COMPANY"));

        StudentProfileResolver resolver = new StudentProfileResolver(profileService, accountService);
        assertThrows(BusinessException.class, resolver::getOrCreateCurrentStudentProfile);
        verify(profileService, never()).getOne(any());
    }
}
