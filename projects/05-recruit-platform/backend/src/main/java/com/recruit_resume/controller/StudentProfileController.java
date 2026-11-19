package com.recruit_resume.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.recruit_resume.common.Result;
import com.recruit_resume.entity.StudentProfile;
import com.recruit_resume.entity.UserAccount;
import com.recruit_resume.security.CurrentUserContext;
import com.recruit_resume.service.StudentProfileService;
import com.recruit_resume.service.UserAccountService;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/student/profiles")
public class StudentProfileController extends BaseCrudController<StudentProfile> {

    private final StudentProfileService service;
    private final UserAccountService userAccountService;

    public StudentProfileController(StudentProfileService service, UserAccountService userAccountService) {
        super(service);
        this.service = service;
        this.userAccountService = userAccountService;
    }

    @GetMapping("/me")
    public Result<StudentProfile> getMyProfile() {
        Long userId = CurrentUserContext.userId();
        StudentProfile profile = service.getOne(new LambdaQueryWrapper<StudentProfile>()
                .eq(StudentProfile::getUserId, userId));
        if (profile == null) {
            profile = new StudentProfile();
            profile.setUserId(userId);
        }
        fillContactFromAccount(profile, userId);
        return Result.success(profile);
    }

    @PutMapping("/me")
    public Result<StudentProfile> updateMyProfile(@Valid @RequestBody StudentProfile body) {
        Long userId = CurrentUserContext.userId();
        body.setUserId(userId);
        StudentProfile existing = service.getOne(new LambdaQueryWrapper<StudentProfile>()
                .eq(StudentProfile::getUserId, userId));
        if (existing != null) {
            body.setId(existing.getId());
        }
        service.saveOrUpdate(body);
        return Result.success(body);
    }

    private void fillContactFromAccount(StudentProfile profile, Long userId) {
        UserAccount account = userAccountService.getById(userId);
        if (account == null) {
            return;
        }
        if (!StringUtils.hasText(profile.getEmail()) && StringUtils.hasText(account.getEmail())) {
            profile.setEmail(account.getEmail());
        }
        if (!StringUtils.hasText(profile.getPhone()) && StringUtils.hasText(account.getPhone())) {
            profile.setPhone(account.getPhone());
        }
    }
}
