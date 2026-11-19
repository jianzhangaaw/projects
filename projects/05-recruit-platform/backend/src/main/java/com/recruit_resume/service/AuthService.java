package com.recruit_resume.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.recruit_resume.common.BusinessException;
import com.recruit_resume.dto.LoginRequest;
import com.recruit_resume.dto.LoginResponse;
import com.recruit_resume.dto.RegisterRequest;
import com.recruit_resume.entity.StudentProfile;
import com.recruit_resume.entity.UserAccount;
import com.recruit_resume.security.JwtTokenProvider;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.Set;

@Slf4j
@Service
public class AuthService {

    // 注册接口对外开放（见 WebMvcConfig 拦截器放行名单），因此禁止通过注册创建 ADMIN，
    // 否则任何未登录用户都能通过 {"role":"ADMIN"} 直接拿到管理员账号，绕过整个鉴权体系。
    // ADMIN 必须由数据库预置或后续运维接口创建。
    private static final Set<String> ALLOWED_ROLES = Set.of("STUDENT", "COMPANY");

    private final UserAccountService userAccountService;
    private final StudentProfileService studentProfileService;
    private final JwtTokenProvider jwtTokenProvider;
    private final LoginAttemptService loginAttemptService;
    private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    public AuthService(
            UserAccountService userAccountService,
            StudentProfileService studentProfileService,
            JwtTokenProvider jwtTokenProvider,
            LoginAttemptService loginAttemptService
    ) {
        this.userAccountService = userAccountService;
        this.studentProfileService = studentProfileService;
        this.jwtTokenProvider = jwtTokenProvider;
        this.loginAttemptService = loginAttemptService;
    }

    public UserAccount register(RegisterRequest request) {
        String username = trimToNull(request.getUsername());
        String password = request.getPassword();
        String role = request.getRole();
        String email = trimToNull(request.getEmail());
        String phone = trimToNull(request.getPhone());

        if (!StringUtils.hasText(username) || !StringUtils.hasText(password)) {
            throw new BusinessException("用户名和密码不能为空");
        }
        if (!ALLOWED_ROLES.contains(role)) {
            throw new BusinessException("角色不合法，仅支持 STUDENT / COMPANY");
        }
        long exists = userAccountService.count(new LambdaQueryWrapper<UserAccount>()
                .eq(UserAccount::getUsername, username));
        if (exists > 0) {
            throw new BusinessException("用户名已被占用");
        }
        if (email != null) {
            long emailExists = userAccountService.count(new LambdaQueryWrapper<UserAccount>()
                    .eq(UserAccount::getEmail, email));
            if (emailExists > 0) {
                throw new BusinessException("邮箱已被占用");
            }
        }
        if (phone != null) {
            long phoneExists = userAccountService.count(new LambdaQueryWrapper<UserAccount>()
                    .eq(UserAccount::getPhone, phone));
            if (phoneExists > 0) {
                throw new BusinessException("手机号已被占用");
            }
        }

        UserAccount account = new UserAccount();
        account.setUsername(username);
        account.setPassword(passwordEncoder.encode(password));
        account.setEmail(email);
        account.setPhone(phone);
        account.setRole(role);
        account.setStatus("ENABLED");
        try {
            userAccountService.save(account);
        } catch (DuplicateKeyException ex) {
            log.warn("注册失败: 用户名/邮箱/手机号重复 username={}", username, ex);
            throw new BusinessException("用户名、邮箱或手机号已被占用");
        }
        createStudentProfileIfNeeded(account);
        account.setPassword(null);
        return account;
    }

    public LoginResponse login(LoginRequest request) {
        String username = request.getUsername();
        // 先看是否在锁定期内，避免锁定后还去做一次 BCrypt 校验（那是 CPU 成本）
        loginAttemptService.assertNotLocked(username);

        UserAccount account = userAccountService.getOne(new LambdaQueryWrapper<UserAccount>()
                .eq(UserAccount::getUsername, username)
                .last("limit 1"));
        if (account == null || !"ENABLED".equals(account.getStatus())) {
            loginAttemptService.recordFailure(username);
            log.warn("登录失败: 账号不存在或已被禁用 username={}", username);
            // 对外与「密码错误」使用同一句提示，避免用户名可枚举
            throw new BusinessException("用户名或密码错误");
        }
        if (!StringUtils.hasText(account.getPassword()) || !passwordEncoder.matches(request.getPassword(), account.getPassword())) {
            loginAttemptService.recordFailure(username);
            log.warn("登录失败: 密码错误 username={}", username);
            throw new BusinessException("用户名或密码错误");
        }
        loginAttemptService.reset(username);

        String token = jwtTokenProvider.createToken(account.getId(), account.getUsername(), account.getRole());
        log.info("登录成功: userId={}, username={}, role={}", account.getId(), account.getUsername(), account.getRole());
        return new LoginResponse(account.getId(), account.getUsername(), account.getRole(), token);
    }

    private String blankToNull(String value) {
        return StringUtils.hasText(value) ? value.trim() : null;
    }

    private String trimToNull(String value) {
        return blankToNull(value);
    }

    private void createStudentProfileIfNeeded(UserAccount account) {
        if (!"STUDENT".equals(account.getRole())) {
            return;
        }
        StudentProfile profile = new StudentProfile();
        profile.setUserId(account.getId());
        profile.setEmail(account.getEmail());
        profile.setPhone(account.getPhone());
        studentProfileService.save(profile);
    }
}
