package com.recruit_resume.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.recruit_resume.common.BusinessException;
import com.recruit_resume.common.ResultCode;
import com.recruit_resume.entity.ResumeSnapshot;
import com.recruit_resume.mapper.ResumeSnapshotMapper;
import com.recruit_resume.security.CurrentUserContext;
import com.recruit_resume.service.ResumeSnapshotService;
import com.recruit_resume.service.StudentProfileResolver;
import org.springframework.stereotype.Service;

@Service
public class ResumeSnapshotServiceImpl extends ServiceImpl<ResumeSnapshotMapper, ResumeSnapshot>
        implements ResumeSnapshotService {

    private final StudentProfileResolver studentProfileResolver;

    public ResumeSnapshotServiceImpl(StudentProfileResolver studentProfileResolver) {
        this.studentProfileResolver = studentProfileResolver;
    }

    @Override
    public ResumeSnapshot getByResumeIdForCurrentStudent(Long resumeId) {
        ResumeSnapshot snapshot = getOne(new LambdaQueryWrapper<ResumeSnapshot>()
                .eq(ResumeSnapshot::getResumeId, resumeId)
                .last("limit 1"));
        if (snapshot == null) {
            throw new BusinessException(ResultCode.NOT_FOUND);
        }
        if (CurrentUserContext.isAdmin()) {
            return snapshot;
        }
        Long currentStudentId = studentProfileResolver.getOrCreateCurrentStudentProfile().getId();
        if (!currentStudentId.equals(snapshot.getStudentId())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        return snapshot;
    }
}
