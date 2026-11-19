package com.recruit_resume.controller;

import com.recruit_resume.common.BusinessException;
import com.recruit_resume.entity.Resume;
import com.recruit_resume.entity.StudentProfile;
import com.recruit_resume.security.CurrentUser;
import com.recruit_resume.security.CurrentUserContext;
import com.recruit_resume.service.FileResourceService;
import com.recruit_resume.service.ResumeGenerationService;
import com.recruit_resume.service.ResumeSnapshotService;
import com.recruit_resume.service.ResumeService;
import com.recruit_resume.service.ResumeTemplateService;
import com.recruit_resume.service.StudentProfileResolver;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class ResumeControllerTest {

    @AfterEach
    void clearCurrentUser() {
        CurrentUserContext.clear();
    }

    @Test
    void createUsesStudentProfileIdInsteadOfUserAccountId() {
        ResumeService resumeService = mock(ResumeService.class);
        FileResourceService fileResourceService = mock(FileResourceService.class);
        StudentProfileResolver studentProfileResolver = mock(StudentProfileResolver.class);
        ResumeGenerationService resumeGenerationService = mock(ResumeGenerationService.class);
        StudentProfile profile = new StudentProfile();
        profile.setId(5L);
        profile.setUserId(40L);
        when(studentProfileResolver.getOrCreateCurrentStudentProfile()).thenReturn(profile);
        ResumeController controller = new ResumeController(
                resumeService,
                fileResourceService,
                studentProfileResolver,
                resumeGenerationService,
                mock(ResumeTemplateService.class),
                mock(ResumeSnapshotService.class)
        );
        CurrentUserContext.set(new CurrentUser(40L, "student", "STUDENT"));

        Resume resume = new Resume();
        resume.setResumeName("简历11");
        resume.setResumeType("UPLOAD");
        resume.setFileId(28L);
        controller.create(resume);

        assertEquals(5L, resume.getStudentId());
        verify(resumeService).save(any(Resume.class));
    }

    @Test
    void generateRejectsNonStudentUser() {
        ResumeController controller = new ResumeController(
                mock(ResumeService.class),
                mock(FileResourceService.class),
                mock(StudentProfileResolver.class),
                mock(ResumeGenerationService.class),
                mock(ResumeTemplateService.class),
                mock(ResumeSnapshotService.class)
        );
        CurrentUserContext.set(new CurrentUser(2L, "company", "COMPANY"));

        BusinessException exception = assertThrows(BusinessException.class, () -> controller.generate(null));

        assertEquals(403, exception.getCode());
    }
}
