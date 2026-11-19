package com.recruit_resume.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.recruit_resume.common.BusinessException;
import com.recruit_resume.dto.GenerateResumeRequest;
import com.recruit_resume.dto.GeneratedResumeResponse;
import com.recruit_resume.dto.ResumeGenerationContextResponse;
import com.recruit_resume.dto.ResumeGenerationSnapshot;
import com.recruit_resume.entity.FileResource;
import com.recruit_resume.entity.Resume;
import com.recruit_resume.entity.ResumeSnapshot;
import com.recruit_resume.entity.ResumeTemplate;
import com.recruit_resume.entity.StudentSkill;
import com.recruit_resume.security.CurrentUserContext;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class ResumeGenerationService {

    private static final String PDF_CONTENT_TYPE = "application/pdf";

    private final ResumeService resumeService;
    private final FileResourceService fileResourceService;
    private final OssStorageService ossStorageService;
    private final ResumeTemplateService templateService;
    private final ResumeSnapshotService snapshotService;
    private final ResumeDataAssembler dataAssembler;
    private final ResumeHtmlRenderService htmlRenderService;
    private final PlaywrightPdfService pdfService;
    private final ObjectMapper objectMapper;

    @Autowired
    public ResumeGenerationService(
            ResumeService resumeService,
            FileResourceService fileResourceService,
            OssStorageService ossStorageService,
            ResumeTemplateService templateService,
            ResumeSnapshotService snapshotService,
            ResumeDataAssembler dataAssembler,
            ResumeHtmlRenderService htmlRenderService,
            PlaywrightPdfService pdfService
    ) {
        this(
                resumeService,
                fileResourceService,
                ossStorageService,
                templateService,
                snapshotService,
                dataAssembler,
                htmlRenderService,
                pdfService,
                new ObjectMapper().findAndRegisterModules()
        );
    }

    public ResumeGenerationService(
            ResumeService resumeService,
            FileResourceService fileResourceService,
            OssStorageService ossStorageService,
            ResumeTemplateService templateService,
            ResumeSnapshotService snapshotService,
            ResumeDataAssembler dataAssembler,
            ResumeHtmlRenderService htmlRenderService,
            PlaywrightPdfService pdfService,
            ObjectMapper objectMapper
    ) {
        this.resumeService = resumeService;
        this.fileResourceService = fileResourceService;
        this.ossStorageService = ossStorageService;
        this.templateService = templateService;
        this.snapshotService = snapshotService;
        this.dataAssembler = dataAssembler;
        this.htmlRenderService = htmlRenderService;
        this.pdfService = pdfService;
        this.objectMapper = objectMapper;
    }

    public ResumeGenerationContextResponse buildContextForCurrentStudent() {
        List<ResumeTemplate> templates = templateService.listActiveTemplates();
        Long defaultTemplateId = templates.isEmpty() ? null : templates.get(0).getId();
        return new ResumeGenerationContextResponse(
                templates,
                defaultTemplateId,
                dataAssembler.buildSnapshotForCurrentStudent()
        );
    }

    @Transactional
    public GeneratedResumeResponse generateForCurrentStudent() {
        ResumeGenerationContextResponse context = buildContextForCurrentStudent();
        return generateForCurrentStudent(new GenerateResumeRequest(context.getDefaultTemplateId(), context.getSnapshot()));
    }

    @Transactional
    public GeneratedResumeResponse generateForCurrentStudent(GenerateResumeRequest request) {
        if (request == null || request.getSnapshot() == null) {
            throw new BusinessException("Resume generation snapshot is required");
        }
        Long studentId = dataAssembler.currentStudentId();
        ResumeGenerationSnapshot snapshot = request.getSnapshot();
        ResumeTemplate template = templateService.requireActiveTemplate(request.getTemplateId());
        String html = htmlRenderService.render(template, snapshot);
        byte[] pdfBytes = pdfService.generatePdf(html);
        FileResource pdfResource = saveGeneratedPdf(snapshot, pdfBytes);
        Resume resume = createResume(studentId, snapshot, pdfResource);
        ResumeSnapshot savedSnapshot = createSnapshot(resume, studentId, template, snapshot, html);
        return new GeneratedResumeResponse(
                resume,
                pdfResource.getId(),
                pdfResource.getFileUrl(),
                savedSnapshot.getId(),
                template.getId()
        );
    }

    private FileResource saveGeneratedPdf(ResumeGenerationSnapshot snapshot, byte[] pdfBytes) {
        String fileName = safeFileName(snapshot.getResumeName()) + ".pdf";
        String url = ossStorageService.upload(fileName, PDF_CONTENT_TYPE, pdfBytes);
        FileResource resource = new FileResource();
        resource.setUploaderId(CurrentUserContext.userId());
        resource.setFileName(fileName);
        resource.setFileType("pdf");
        resource.setFileUrl(url);
        resource.setFileSize((long) pdfBytes.length);
        resource.setBusinessType("RESUME");
        fileResourceService.save(resource);
        return resource;
    }

    private Resume createResume(Long studentId, ResumeGenerationSnapshot snapshot, FileResource pdfResource) {
        Resume resume = new Resume();
        resume.setStudentId(studentId);
        resume.setResumeName(StringUtils.hasText(snapshot.getResumeName())
                ? snapshot.getResumeName()
                : "Generated Resume");
        resume.setResumeType("ONLINE");
        resume.setTargetPosition(snapshot.getTargetPosition());
        resume.setFileId(pdfResource.getId());
        resume.setFileUrl(pdfResource.getFileUrl());
        if (snapshot.getProfile() != null) {
            resume.setSchool(snapshot.getProfile().getSchool());
            resume.setMajor(snapshot.getProfile().getMajor());
            resume.setEducationLevel(snapshot.getProfile().getEducationLevel());
            resume.setGraduationDate(snapshot.getProfile().getGraduationDate());
        }
        if (snapshot.getSkills() != null) {
            resume.setSkillTags(snapshot.getSkills().stream()
                    .map(StudentSkill::getSkillName)
                    .filter(StringUtils::hasText)
                    .collect(Collectors.joining(", ")));
        }
        resumeService.save(resume);
        return resume;
    }

    private ResumeSnapshot createSnapshot(
            Resume resume,
            Long studentId,
            ResumeTemplate template,
            ResumeGenerationSnapshot snapshot,
            String html
    ) {
        ResumeSnapshot savedSnapshot = new ResumeSnapshot();
        savedSnapshot.setResumeId(resume.getId());
        savedSnapshot.setStudentId(studentId);
        savedSnapshot.setTemplateId(template.getId());
        savedSnapshot.setSnapshotJson(writeSnapshotJson(snapshot));
        savedSnapshot.setHtmlContent(html);
        savedSnapshot.setGeneratedAt(LocalDateTime.now());
        snapshotService.save(savedSnapshot);
        return savedSnapshot;
    }

    private String writeSnapshotJson(ResumeGenerationSnapshot snapshot) {
        try {
            return objectMapper.writeValueAsString(snapshot);
        } catch (JsonProcessingException ex) {
            throw new BusinessException("Resume snapshot serialization failed");
        }
    }

    private String safeFileName(String fileName) {
        String baseName = StringUtils.hasText(fileName) ? fileName : "generated-resume";
        String sanitized = baseName.replaceAll("[\\\\/:*?\"<>|\\s]+", "-");
        return StringUtils.hasText(sanitized) ? sanitized : "generated-resume";
    }
}
