package com.recruit_resume.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.recruit_resume.entity.FileResource;
import com.recruit_resume.mapper.FileResourceMapper;
import com.recruit_resume.service.FileResourceService;
import org.springframework.stereotype.Service;

@Service
public class FileResourceServiceImpl extends ServiceImpl<FileResourceMapper, FileResource> implements FileResourceService {
}
