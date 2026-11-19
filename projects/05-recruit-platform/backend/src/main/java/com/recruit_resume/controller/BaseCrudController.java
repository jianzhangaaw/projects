package com.recruit_resume.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.IService;
import com.recruit_resume.common.Result;
import com.recruit_resume.common.PageQuery;
import jakarta.validation.Valid;
import org.springframework.beans.BeanWrapper;
import org.springframework.beans.BeanWrapperImpl;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;

public abstract class BaseCrudController<T> {

    private final IService<T> service;

    protected BaseCrudController(IService<T> service) {
        this.service = service;
    }

    @GetMapping
    public Result<IPage<T>> page(@Valid PageQuery query) {
        return Result.success(service.page(Page.of(query.getCurrent(), query.getSize())));
    }

    @GetMapping("/{id}")
    public Result<T> get(@PathVariable Long id) {
        return Result.success(service.getById(id));
    }

    @PostMapping
    public Result<T> create(@RequestBody T body) {
        service.save(body);
        return Result.success(body);
    }

    @PutMapping("/{id}")
    public Result<T> update(@PathVariable Long id, @RequestBody T body) {
        BeanWrapper wrapper = new BeanWrapperImpl(body);
        if (wrapper.isWritableProperty("id")) {
            wrapper.setPropertyValue("id", id);
        }
        service.updateById(body);
        return Result.success(body);
    }

    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        service.removeById(id);
        return Result.success();
    }
}
