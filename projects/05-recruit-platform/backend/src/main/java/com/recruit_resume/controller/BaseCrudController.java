package com.recruit_resume.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.IService;
import com.recruit_resume.common.BusinessException;
import com.recruit_resume.common.Result;
import com.recruit_resume.common.PageQuery;
import com.recruit_resume.common.ResultCode;
import com.recruit_resume.security.CurrentUser;
import com.recruit_resume.security.CurrentUserContext;
import jakarta.validation.Valid;
import org.springframework.beans.BeanWrapper;
import org.springframework.beans.BeanWrapperImpl;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;

/**
 * 泛型 CRUD 基类。
 *
 * <p>注意：这里只做「这条记录是不是当前用户的」这一层校验（{@link #isOwnedBy}）。
 * 角色校验由 {@code JwtAuthInterceptor} 按 URL 前缀负责，所以本类里的 get / update / delete
 * 只对已通过角色校验的请求生效。
 *
 * <p>历史问题：早期版本这三个方法直接按 id 读写，只要角色对就能操作任意记录（水平越权）。
 * 现在要求子类必须实现 {@link #isOwnedBy}，找不到记录返回 404、不属于自己返回 403。
 */
public abstract class BaseCrudController<T> {

    protected final IService<T> service;

    protected BaseCrudController(IService<T> service) {
        this.service = service;
    }

    /**
     * 判断这条记录是否属于当前登录用户。
     *
     * <p>子类必须实现，没有默认实现是刻意的——漏实现会编译不过，而不是悄悄放行。
     * 不同实体的归属字段不同（Company.userId / Job.companyId / Resume.studentId ...），
     * 由子类决定怎么查。
     */
    protected abstract boolean isOwnedBy(T entity, CurrentUser user);

    @GetMapping
    public Result<IPage<T>> page(@Valid PageQuery query) {
        return Result.success(service.page(Page.of(query.getCurrent(), query.getSize())));
    }

    @GetMapping("/{id}")
    public Result<T> get(@PathVariable Long id) {
        return Result.success(requireOwned(id));
    }

    @PostMapping
    public Result<T> create(@RequestBody T body) {
        service.save(body);
        return Result.success(body);
    }

    @PutMapping("/{id}")
    public Result<T> update(@PathVariable Long id, @RequestBody T body) {
        requireOwned(id);
        BeanWrapper wrapper = new BeanWrapperImpl(body);
        if (wrapper.isWritableProperty("id")) {
            wrapper.setPropertyValue("id", id);
        }
        service.updateById(body);
        return Result.success(body);
    }

    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        requireOwned(id);
        service.removeById(id);
        return Result.success();
    }

    /**
     * 按 id 取记录并校验归属；不存在抛 404，不属于当前用户抛 403。
     */
    protected T requireOwned(Long id) {
        T entity = service.getById(id);
        if (entity == null) {
            throw new BusinessException(ResultCode.NOT_FOUND);
        }
        if (!isOwnedBy(entity, CurrentUserContext.require())) {
            throw new BusinessException(ResultCode.FORBIDDEN);
        }
        return entity;
    }
}
