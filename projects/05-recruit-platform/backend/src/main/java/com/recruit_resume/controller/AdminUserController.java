package com.recruit_resume.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.recruit_resume.common.BusinessException;
import com.recruit_resume.common.PageQuery;
import com.recruit_resume.common.Result;
import com.recruit_resume.entity.Company;
import com.recruit_resume.entity.StudentProfile;
import com.recruit_resume.entity.UserAccount;
import com.recruit_resume.security.CurrentUserContext;
import com.recruit_resume.service.CompanyService;
import com.recruit_resume.service.StudentProfileService;
import com.recruit_resume.service.UserAccountService;
import jakarta.validation.Valid;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/admin/users")
public class AdminUserController {

    private final UserAccountService service;
    private final StudentProfileService studentProfileService;
    private final CompanyService companyService;

    public AdminUserController(UserAccountService service, StudentProfileService studentProfileService, CompanyService companyService) {
        this.service = service;
        this.studentProfileService = studentProfileService;
        this.companyService = companyService;
    }

    @GetMapping
    public Result<IPage<UserAccount>> page(
            @Valid PageQuery query,
            @RequestParam(required = false) String username,
            @RequestParam(required = false) String role,
            @RequestParam(required = false) String status
    ) {
        LambdaQueryWrapper<UserAccount> wrapper = new LambdaQueryWrapper<UserAccount>()
                .like(StringUtils.hasText(username), UserAccount::getUsername, username)
                .eq(StringUtils.hasText(role), UserAccount::getRole, role)
                .eq(StringUtils.hasText(status), UserAccount::getStatus, status)
                .orderByDesc(UserAccount::getCreatedAt);
        IPage<UserAccount> page = service.page(Page.of(query.getCurrent(), query.getSize()), wrapper);
        page.getRecords().forEach(this::erasePassword);
        fillAssociatedNames(page.getRecords());
        return Result.success(page);
    }

    private void fillAssociatedNames(List<UserAccount> users) {
        List<Long> studentUserIds = users.stream()
                .filter(u -> "STUDENT".equals(u.getRole()))
                .map(UserAccount::getId).toList();
        List<Long> companyUserIds = users.stream()
                .filter(u -> "COMPANY".equals(u.getRole()))
                .map(UserAccount::getId).toList();

        Map<Long, String> studentNameMap = Map.of();
        if (!studentUserIds.isEmpty()) {
            studentNameMap = studentProfileService.list(new LambdaQueryWrapper<StudentProfile>()
                            .in(StudentProfile::getUserId, studentUserIds))
                    .stream().collect(Collectors.toMap(StudentProfile::getUserId, s ->
                            s.getRealName() != null ? s.getRealName() : "", (a, b) -> a));
        }

        Map<Long, String> companyNameMap = Map.of();
        if (!companyUserIds.isEmpty()) {
            companyNameMap = companyService.list(new LambdaQueryWrapper<Company>()
                            .in(Company::getUserId, companyUserIds))
                    .stream().collect(Collectors.toMap(Company::getUserId, c ->
                            c.getCompanyName() != null ? c.getCompanyName() : "", (a, b) -> a));
        }

        for (UserAccount u : users) {
            if ("STUDENT".equals(u.getRole())) {
                u.setAssociatedName(studentNameMap.getOrDefault(u.getId(), ""));
            } else if ("COMPANY".equals(u.getRole())) {
                u.setAssociatedName(companyNameMap.getOrDefault(u.getId(), ""));
            }
        }
    }

    @PatchMapping("/{id}/status")
    public Result<Void> updateStatus(@PathVariable Long id, @RequestParam String status) {
        return doUpdateStatus(id, status);
    }

    @PutMapping("/{id}/status")
    public Result<Void> updateStatusByPut(@PathVariable Long id, @RequestParam String status) {
        return doUpdateStatus(id, status);
    }

    private Result<Void> doUpdateStatus(Long id, String status) {
        if (!"ENABLED".equals(status) && !"DISABLED".equals(status)) {
            throw new BusinessException("账号状态只能是 ENABLED 或 DISABLED");
        }
        if (CurrentUserContext.userId().equals(id) && "DISABLED".equals(status)) {
            throw new BusinessException("不能禁用当前登录的管理员账号");
        }
        UserAccount existing = service.getById(id);
        if (existing == null) {
            throw new BusinessException("用户不存在");
        }
        UserAccount account = new UserAccount();
        account.setId(id);
        account.setStatus(status);
        service.updateById(account);
        return Result.success();
    }

    private void erasePassword(UserAccount account) {
        account.setPassword(null);
    }
}
