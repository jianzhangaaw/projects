package com.recruit_resume.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.recruit_resume.common.BusinessException;
import com.recruit_resume.common.PageQuery;
import com.recruit_resume.common.Result;
import com.recruit_resume.common.ResultCode;
import com.recruit_resume.entity.Notification;
import com.recruit_resume.security.CurrentUserContext;
import com.recruit_resume.service.NotificationService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/notifications")
public class NotificationController {

    private final NotificationService service;

    public NotificationController(NotificationService service) {
        this.service = service;
    }

    @GetMapping
    public Result<IPage<Notification>> page(
            @Valid PageQuery query,
            @RequestParam(required = false) Integer isRead
    ) {
        LambdaQueryWrapper<Notification> wrapper = currentUserWrapper()
                .eq(isRead != null, Notification::getIsRead, isRead)
                .orderByDesc(Notification::getCreatedAt);
        return Result.success(service.page(Page.of(query.getCurrent(), query.getSize()), wrapper));
    }

    @GetMapping("/mine")
    public Result<List<Notification>> mine(@RequestParam(required = false) Long receiverId) {
        return Result.success(service.list(currentUserWrapper()
                .orderByDesc(Notification::getCreatedAt)));
    }

    @PatchMapping("/{id}/read")
    public Result<Void> markRead(@PathVariable Long id) {
        return doMarkRead(id);
    }

    @PutMapping("/{id}/read")
    public Result<Void> markReadByPut(@PathVariable Long id) {
        return doMarkRead(id);
    }

    @PatchMapping("/read-all")
    public Result<Void> markAllRead() {
        service.update(new LambdaUpdateWrapper<Notification>()
                .eq(Notification::getReceiverId, CurrentUserContext.userId())
                .eq(Notification::getIsRead, 0)
                .set(Notification::getIsRead, 1));
        return Result.success();
    }

    @PutMapping("/read-all")
    public Result<Void> markAllReadByPut() {
        return markAllRead();
    }

    private Result<Void> doMarkRead(Long id) {
        Notification existing = service.getById(id);
        if (existing == null) {
            throw new BusinessException(ResultCode.NOT_FOUND);
        }
        if (!CurrentUserContext.userId().equals(existing.getReceiverId())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        Notification notification = new Notification();
        notification.setId(id);
        notification.setIsRead(1);
        service.updateById(notification);
        return Result.success();
    }

    @GetMapping("/unread-count")
    public Result<Long> unreadCount() {
        long count = service.count(new LambdaQueryWrapper<Notification>()
                .eq(Notification::getReceiverId, CurrentUserContext.userId())
                .eq(Notification::getIsRead, 0));
        return Result.success(count);
    }

    private LambdaQueryWrapper<Notification> currentUserWrapper() {
        return new LambdaQueryWrapper<Notification>()
                .eq(Notification::getReceiverId, CurrentUserContext.userId());
    }
}
