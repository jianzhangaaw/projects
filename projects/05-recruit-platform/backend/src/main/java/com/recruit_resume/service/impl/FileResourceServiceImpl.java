package com.recruit_resume.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.recruit_resume.entity.FileResource;
import com.recruit_resume.mapper.FileResourceMapper;
import com.recruit_resume.service.FileResourceService;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

@Service
public class FileResourceServiceImpl extends ServiceImpl<FileResourceMapper, FileResource> implements FileResourceService {

    @Override
    public Map<Long, String> fileUrlsByIds(Collection<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return Map.of();
        }
        List<Long> distinct = ids.stream().filter(Objects::nonNull).distinct().toList();
        if (distinct.isEmpty()) {
            return Map.of();
        }
        Map<Long, String> urls = new HashMap<>();
        for (FileResource resource : listByIds(distinct)) {
            if (resource.getId() != null && StringUtils.hasText(resource.getFileUrl())) {
                urls.put(resource.getId(), resource.getFileUrl());
            }
        }
        return urls;
    }
}
