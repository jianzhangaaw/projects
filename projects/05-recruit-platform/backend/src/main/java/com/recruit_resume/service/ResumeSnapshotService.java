package com.recruit_resume.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.recruit_resume.entity.ResumeSnapshot;

public interface ResumeSnapshotService extends IService<ResumeSnapshot> {

    ResumeSnapshot getByResumeIdForCurrentStudent(Long resumeId);
}
