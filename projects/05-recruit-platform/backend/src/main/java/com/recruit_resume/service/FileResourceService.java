package com.recruit_resume.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.recruit_resume.entity.FileResource;

import java.util.Collection;
import java.util.Map;

public interface FileResourceService extends IService<FileResource> {

    /**
     * 批量取文件访问地址：fileResourceId -> fileUrl。
     *
     * <p>列表接口原来在 forEach 里逐条 getById（N 条简历就是 N 次查询），
     * 现在一次 listByIds 拿回来。查不到的、fileUrl 为空的不进结果，调用方按缺失处理。
     */
    Map<Long, String> fileUrlsByIds(Collection<Long> ids);
}
