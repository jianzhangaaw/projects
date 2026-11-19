package com.recruit_resume.controller;

import com.recruit_resume.common.BusinessException;
import com.recruit_resume.entity.FileResource;
import com.recruit_resume.security.CurrentUser;
import com.recruit_resume.security.CurrentUserContext;
import com.recruit_resume.service.FilePreviewService;
import com.recruit_resume.service.FileResourceService;
import com.recruit_resume.service.OssStorageService;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.mock.web.MockMultipartFile;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class FileResourceControllerTest {

    @AfterEach
    void clearCurrentUser() {
        CurrentUserContext.clear();
    }

    @Test
    void previewKeepsFileAccessControl() throws Exception {
        FileResourceService fileResourceService = mock(FileResourceService.class);
        OssStorageService ossStorageService = mock(OssStorageService.class);
        FilePreviewService filePreviewService = mock(FilePreviewService.class);
        FileResource resource = new FileResource();
        resource.setId(11L);
        resource.setUploaderId(99L);
        resource.setBusinessType("RESUME");
        when(fileResourceService.getById(11L)).thenReturn(resource);
        CurrentUserContext.set(new CurrentUser(7L, "student", "STUDENT"));
        FileResourceController controller = new FileResourceController(
                fileResourceService,
                ossStorageService,
                filePreviewService
        );

        BusinessException exception = assertThrows(
                BusinessException.class,
                () -> controller.preview(11L, new MockHttpServletResponse())
        );

        assertEquals(403, exception.getCode());
        verify(filePreviewService, never()).writePreview(resource, new MockHttpServletResponse());
    }

    @Test
    void uploadStoresShortFileTypeForWordResume() throws Exception {
        FileResourceService fileResourceService = mock(FileResourceService.class);
        OssStorageService ossStorageService = mock(OssStorageService.class);
        FilePreviewService filePreviewService = mock(FilePreviewService.class);
        when(ossStorageService.upload(any())).thenReturn("https://example.com/resume.docx");
        doAnswer(invocation -> {
            FileResource resource = invocation.getArgument(0);
            resource.setId(22L);
            return true;
        }).when(fileResourceService).save(any(FileResource.class));
        CurrentUserContext.set(new CurrentUser(40L, "student", "STUDENT"));
        FileResourceController controller = new FileResourceController(
                fileResourceService,
                ossStorageService,
                filePreviewService
        );
        MockMultipartFile file = new MockMultipartFile(
                "file",
                "ZWW-00079市场营销专业实习生简历模板.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "resume".getBytes()
        );

        controller.upload("RESUME", null, file);

        verify(fileResourceService).save(any(FileResource.class));
        verify(fileResourceService).save(org.mockito.ArgumentMatchers.argThat(resource ->
                resource.getUploaderId().equals(40L)
                        && "RESUME".equals(resource.getBusinessType())
                        && "docx".equals(resource.getFileType())
                        && "ZWW-00079市场营销专业实习生简历模板.docx".equals(resource.getFileName())
        ));
    }
}
