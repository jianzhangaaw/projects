package com.recruit_resume.security;

import com.recruit_resume.common.BusinessException;
import com.recruit_resume.common.ResultCode;

public final class CurrentUserContext {

    private static final ThreadLocal<CurrentUser> HOLDER = new ThreadLocal<>();

    private CurrentUserContext() {
    }

    public static void set(CurrentUser currentUser) {
        HOLDER.set(currentUser);
    }

    public static CurrentUser get() {
        return HOLDER.get();
    }

    public static CurrentUser require() {
        CurrentUser currentUser = get();
        if (currentUser == null) {
            throw new BusinessException(ResultCode.UNAUTHORIZED);
        }
        return currentUser;
    }

    public static Long userId() {
        return require().getUserId();
    }

    public static String role() {
        return require().getRole();
    }

    public static boolean isAdmin() {
        return "ADMIN".equals(role());
    }

    public static void requireRole(String role) {
        CurrentUser currentUser = require();
        if (!role.equals(currentUser.getRole())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
    }

    public static void clear() {
        HOLDER.remove();
    }
}
