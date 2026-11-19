package com.recruit_resume.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.recruit_resume.common.BusinessException;
import com.recruit_resume.common.ResultCode;
import com.recruit_resume.entity.StudentProfile;
import com.recruit_resume.entity.UserAccount;
import com.recruit_resume.security.CurrentUser;
import com.recruit_resume.security.CurrentUserContext;
import org.springframework.stereotype.Service;

@Service
public class StudentProfileResolver {

    private final StudentProfileService studentProfileService;
    private final UserAccountService userAccountService;

    public StudentProfileResolver(StudentProfileService studentProfileService, UserAccountService userAccountService) {
        this.studentProfileService = studentProfileService;
        this.userAccountService = userAccountService;
    }

    public StudentProfile getOrCreateCurrentStudentProfile() {
        CurrentUser currentUser = CurrentUserContext.require();
        if (!"STUDENT".equals(currentUser.getRole())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        StudentProfile profile = studentProfileService.getOne(new LambdaQueryWrapper<StudentProfile>()
                .eq(StudentProfile::getUserId, currentUser.getUserId())
                .last("limit 1"));
        if (profile != null) {
            return profile;
        }
        UserAccount account = userAccountService.getById(currentUser.getUserId());
        profile = new StudentProfile();
        profile.setUserId(currentUser.getUserId());
        if (account != null) {
            profile.setEmail(account.getEmail());
            profile.setPhone(account.getPhone());
        }
        studentProfileService.save(profile);
        return profile;
    }
}
