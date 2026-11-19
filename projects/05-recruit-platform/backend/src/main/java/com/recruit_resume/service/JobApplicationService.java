package com.recruit_resume.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.IService;
import com.recruit_resume.dto.CompanyApplicationDetail;
import com.recruit_resume.dto.StudentApplicationDetail;
import com.recruit_resume.entity.JobApplication;

import java.util.List;

/**
 * 投递相关的业务逻辑。
 *
 * <p>方法都以 {@code userId} / {@code role} 作显式参数，不直接读 {@code CurrentUserContext}——
 * 这样单测里不需要伪造 ThreadLocal，也避免 Service 层悄悄依赖 Web 上下文。
 */
public interface JobApplicationService extends IService<JobApplication> {

    /**
     * 学生投递岗位。校验岗位已发布、简历属于本人、未重复投递；投递成功后在同一个事务里给企业发通知。
     *
     * @throws com.recruit_resume.common.BusinessException 岗位不存在/未发布、简历不属于本人、重复投递、学生资料不完整
     */
    JobApplication apply(Long userId, Long jobId, Long resumeId);

    /** 学生撤回投递，只有 PENDING 状态可以撤回。 */
    void withdraw(Long userId, Long applicationId);

    /**
     * 企业或管理员更新投递状态。
     * 状态机：PENDING → PASSED / REJECTED，已终态不可再改。
     */
    void updateStatus(Long userId, String role, Long applicationId, String status, String remark);

    /** 按角色分页：学生只看自己的、企业只看收到的、管理员看全部。 */
    IPage<JobApplication> pageForUser(Long userId, String role, long current, long size);

    List<JobApplication> listByStudent(Long userId);

    List<JobApplication> listByCompany(Long userId);

    /** 学生端投递详情（带岗位与企业名称），批量装配，不做逐条查询。 */
    List<StudentApplicationDetail> listStudentDetails(Long userId);

    /** 企业端投递详情（带学生与简历信息），批量装配。 */
    List<CompanyApplicationDetail> listCompanyDetails(Long userId);
}
