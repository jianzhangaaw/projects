package com.recruit_resume.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.recruit_resume.common.BusinessException;
import com.recruit_resume.common.RequestCache;
import com.recruit_resume.common.ResultCode;
import com.recruit_resume.entity.StudentProfile;
import com.recruit_resume.entity.UserAccount;
import com.recruit_resume.security.CurrentUser;
import com.recruit_resume.security.CurrentUserContext;
import org.springframework.stereotype.Service;

@Service
public class StudentProfileResolver {

    private static final String CACHE_KEY_PREFIX = "studentProfile:";

    private final StudentProfileService studentProfileService;
    private final UserAccountService userAccountService;

    public StudentProfileResolver(StudentProfileService studentProfileService, UserAccountService userAccountService) {
        this.studentProfileService = studentProfileService;
        this.userAccountService = userAccountService;
    }

    /**
     * 取当前登录学生的资料，没有就建一条。
     *
     * <p>结果进 {@link RequestCache}：同一个请求里反复调用（Controller 取一次、
     * Service 里再取一次）只查一次库。缓存按 userId 分 key，同一请求内换用户不会串数据。
     */
    public StudentProfile getOrCreateCurrentStudentProfile() {
        CurrentUser currentUser = CurrentUserContext.require();
        if (!"STUDENT".equals(currentUser.getRole())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        String cacheKey = CACHE_KEY_PREFIX + currentUser.getUserId();
        StudentProfile cached = RequestCache.get(cacheKey, StudentProfile.class);
        if (cached != null) {
            return cached;
        }
        StudentProfile profile = studentProfileService.getOne(new LambdaQueryWrapper<StudentProfile>()
                .eq(StudentProfile::getUserId, currentUser.getUserId())
                .last("limit 1"));
        if (profile == null) {
            UserAccount account = userAccountService.getById(currentUser.getUserId());
            profile = new StudentProfile();
            profile.setUserId(currentUser.getUserId());
            if (account != null) {
                profile.setEmail(account.getEmail());
                profile.setPhone(account.getPhone());
            }
            studentProfileService.save(profile);
        }
        RequestCache.put(cacheKey, profile);
        return profile;
    }
}
