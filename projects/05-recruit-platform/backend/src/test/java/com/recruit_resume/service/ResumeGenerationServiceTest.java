package com.recruit_resume.service;

import com.recruit_resume.common.BusinessException;
import com.recruit_resume.dto.GenerateResumeRequest;
import com.recruit_resume.dto.GeneratedResumeResponse;
import com.recruit_resume.dto.ResumeGenerationSnapshot;
import com.recruit_resume.entity.FileResource;
import com.recruit_resume.entity.Resume;
import com.recruit_resume.entity.ResumeSnapshot;
import com.recruit_resume.entity.ResumeTemplate;
import com.recruit_resume.entity.StudentExperience;
import com.recruit_resume.entity.StudentProfile;
import com.recruit_resume.entity.StudentSkill;
import com.recruit_resume.security.CurrentUser;
import com.recruit_resume.security.CurrentUserContext;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.when;

class ResumeGenerationServiceTest {

    @AfterEach
    void clearCurrentUser() {
        CurrentUserContext.clear();
    }

    @Test
    void generatesPdfThenCreatesResumeAndSnapshot() {
        CurrentUserContext.set(new CurrentUser(40L, "student", "STUDENT"));
        ResumeService resumeService = mock(ResumeService.class);
        FileResourceService fileResourceService = mock(FileResourceService.class);
        OssStorageService ossStorageService = mock(OssStorageService.class);
        ResumeTemplateService templateService = mock(ResumeTemplateService.class);
        ResumeSnapshotService snapshotService = mock(ResumeSnapshotService.class);
        ResumeDataAssembler dataAssembler = mock(ResumeDataAssembler.class);
        ResumeHtmlRenderService htmlRenderService = mock(ResumeHtmlRenderService.class);
        PlaywrightPdfService pdfService = mock(PlaywrightPdfService.class);
        ResumeTemplate template = template();
        ResumeGenerationSnapshot snapshot = snapshot("Java Backend Resume");
        when(dataAssembler.currentStudentId()).thenReturn(20L);
        when(templateService.requireActiveTemplate(5L)).thenReturn(template);
        when(htmlRenderService.render(template, snapshot)).thenReturn("<html>resume</html>");
        when(pdfService.generatePdf("<html>resume</html>")).thenReturn("%PDF-1.4".getBytes());
        when(ossStorageService.upload(any(String.class), eq("application/pdf"), any(byte[].class)))
                .thenReturn("https://oss/resume.pdf");
        doAnswer(invocation -> {
            FileResource resource = invocation.getArgument(0);
            resource.setId(81L);
            return true;
        }).when(fileResourceService).save(any(FileResource.class));
        doAnswer(invocation -> {
            Resume resume = invocation.getArgument(0);
            resume.setId(99L);
            return true;
        }).when(resumeService).save(any(Resume.class));
        doAnswer(invocation -> {
            ResumeSnapshot saved = invocation.getArgument(0);
            saved.setId(120L);
            return true;
        }).when(snapshotService).save(any(ResumeSnapshot.class));
        ResumeGenerationService service = service(
                resumeService,
                fileResourceService,
                ossStorageService,
                templateService,
                snapshotService,
                dataAssembler,
                htmlRenderService,
                pdfService
        );

        GeneratedResumeResponse response = service.generateForCurrentStudent(new GenerateResumeRequest(5L, snapshot));

        assertEquals(99L, response.getResume().getId());
        assertEquals(81L, response.getPdfFileId());
        assertEquals("https://oss/resume.pdf", response.getPdfFileUrl());
        assertEquals(120L, response.getSnapshotId());
        assertEquals(5L, response.getTemplateId());
        verify(resumeService).save(any(Resume.class));
        verify(snapshotService).save(any(ResumeSnapshot.class));
    }

    @Test
    void pdfFailureDoesNotCreateResumeOrSnapshot() {
        CurrentUserContext.set(new CurrentUser(40L, "student", "STUDENT"));
        ResumeService resumeService = mock(ResumeService.class);
        FileResourceService fileResourceService = mock(FileResourceService.class);
        OssStorageService ossStorageService = mock(OssStorageService.class);
        ResumeTemplateService templateService = mock(ResumeTemplateService.class);
        ResumeSnapshotService snapshotService = mock(ResumeSnapshotService.class);
        ResumeDataAssembler dataAssembler = mock(ResumeDataAssembler.class);
        ResumeHtmlRenderService htmlRenderService = mock(ResumeHtmlRenderService.class);
        PlaywrightPdfService pdfService = mock(PlaywrightPdfService.class);
        ResumeTemplate template = template();
        ResumeGenerationSnapshot snapshot = snapshot("Java Backend Resume");
        when(dataAssembler.currentStudentId()).thenReturn(20L);
        when(templateService.requireActiveTemplate(5L)).thenReturn(template);
        when(htmlRenderService.render(template, snapshot)).thenReturn("<html>resume</html>");
        when(pdfService.generatePdf("<html>resume</html>"))
                .thenThrow(new BusinessException("PDF generation failed"));
        ResumeGenerationService service = service(
                resumeService,
                fileResourceService,
                ossStorageService,
                templateService,
                snapshotService,
                dataAssembler,
                htmlRenderService,
                pdfService
        );

        assertThrows(BusinessException.class,
                () -> service.generateForCurrentStudent(new GenerateResumeRequest(5L, snapshot)));

        verify(ossStorageService, never()).upload(any(String.class), any(String.class), any(byte[].class));
        verify(fileResourceService, never()).save(any(FileResource.class));
        verify(resumeService, never()).save(any(Resume.class));
        verify(snapshotService, never()).save(any(ResumeSnapshot.class));
    }

    @Test
    void repeatedGenerationCreatesIndependentResumeRecords() {
        CurrentUserContext.set(new CurrentUser(40L, "student", "STUDENT"));
        ResumeService resumeService = mock(ResumeService.class);
        FileResourceService fileResourceService = mock(FileResourceService.class);
        OssStorageService ossStorageService = mock(OssStorageService.class);
        ResumeTemplateService templateService = mock(ResumeTemplateService.class);
        ResumeSnapshotService snapshotService = mock(ResumeSnapshotService.class);
        ResumeDataAssembler dataAssembler = mock(ResumeDataAssembler.class);
        ResumeHtmlRenderService htmlRenderService = mock(ResumeHtmlRenderService.class);
        PlaywrightPdfService pdfService = mock(PlaywrightPdfService.class);
        ResumeTemplate template = template();
        ResumeGenerationSnapshot snapshot = snapshot("Java Backend Resume");
        when(dataAssembler.currentStudentId()).thenReturn(20L);
        AtomicLong fileIds = new AtomicLong(80L);
        AtomicLong resumeIds = new AtomicLong(98L);
        AtomicLong snapshotIds = new AtomicLong(118L);
        when(templateService.requireActiveTemplate(5L)).thenReturn(template);
        when(htmlRenderService.render(template, snapshot)).thenReturn("<html>resume</html>");
        when(pdfService.generatePdf("<html>resume</html>")).thenReturn("%PDF-1.4".getBytes());
        when(ossStorageService.upload(any(String.class), eq("application/pdf"), any(byte[].class)))
                .thenReturn("https://oss/resume-1.pdf")
                .thenReturn("https://oss/resume-2.pdf");
        doAnswer(invocation -> {
            FileResource resource = invocation.getArgument(0);
            resource.setId(fileIds.incrementAndGet());
            return true;
        }).when(fileResourceService).save(any(FileResource.class));
        doAnswer(invocation -> {
            Resume resume = invocation.getArgument(0);
            resume.setId(resumeIds.incrementAndGet());
            return true;
        }).when(resumeService).save(any(Resume.class));
        doAnswer(invocation -> {
            ResumeSnapshot saved = invocation.getArgument(0);
            saved.setId(snapshotIds.incrementAndGet());
            return true;
        }).when(snapshotService).save(any(ResumeSnapshot.class));
        ResumeGenerationService service = service(
                resumeService,
                fileResourceService,
                ossStorageService,
                templateService,
                snapshotService,
                dataAssembler,
                htmlRenderService,
                pdfService
        );

        GeneratedResumeResponse first = service.generateForCurrentStudent(new GenerateResumeRequest(5L, snapshot));
        GeneratedResumeResponse second = service.generateForCurrentStudent(new GenerateResumeRequest(5L, snapshot));

        assertNotNull(first.getResume());
        assertNotNull(second.getResume());
        assertEquals(99L, first.getResume().getId());
        assertEquals(100L, second.getResume().getId());
        assertEquals(119L, first.getSnapshotId());
        assertEquals(120L, second.getSnapshotId());
        verify(resumeService, times(2)).save(any(Resume.class));
        verify(snapshotService, times(2)).save(any(ResumeSnapshot.class));
    }

    private ResumeGenerationService service(
            ResumeService resumeService,
            FileResourceService fileResourceService,
            OssStorageService ossStorageService,
            ResumeTemplateService templateService,
            ResumeSnapshotService snapshotService,
            ResumeDataAssembler dataAssembler,
            ResumeHtmlRenderService htmlRenderService,
            PlaywrightPdfService pdfService
    ) {
        return new ResumeGenerationService(
                resumeService,
                fileResourceService,
                ossStorageService,
                templateService,
                snapshotService,
                dataAssembler,
                htmlRenderService,
                pdfService
        );
    }

    private ResumeTemplate template() {
        ResumeTemplate template = new ResumeTemplate();
        template.setId(5L);
        template.setTemplateCode("classic");
        template.setTemplateName("Classic");
        template.setEnabled(1);
        template.setVersion(1);
        return template;
    }

    private ResumeGenerationSnapshot snapshot(String resumeName) {
        StudentProfile profile = new StudentProfile();
        profile.setId(20L);
        profile.setUserId(40L);
        profile.setRealName("Zhang San");
        profile.setPhone("13800000000");
        profile.setEmail("zhang@example.com");
        profile.setSchool("BUPT");
        profile.setMajor("Software Engineering");
        profile.setEducationLevel("Bachelor");
        profile.setGraduationDate(LocalDate.of(2026, 7, 1));
        profile.setExpectedPosition("Java Backend");
        profile.setExpectedCity("Beijing");
        profile.setSelfIntro("Enjoys engineering practice");
        StudentSkill skill = new StudentSkill();
        skill.setSkillName("Java");
        skill.setSkillType("Programming");
        skill.setProficiency("Skilled");
        skill.setYears(BigDecimal.valueOf(2));
        StudentExperience experience = new StudentExperience();
        experience.setExperienceType("PROJECT");
        experience.setTitle("Campus Recruiting Platform");
        experience.setTimeRange("2025.09-2026.01");
        experience.setRoleName("Backend Developer");
        experience.setDescription("Built resume delivery and review modules");
        return new ResumeGenerationSnapshot(
                resumeName,
                "Java Backend",
                profile,
                List.of(skill),
                List.of(experience)
        );
    }
}
