package com.recruit_resume.service;

import com.recruit_resume.entity.Company;
import com.recruit_resume.entity.Job;

import java.util.List;

/**
 * 管理员审核（企业入驻 / 企业资料修改 / 岗位发布）。
 *
 * <p>三个审核动作各自是一个事务：改主表、删草稿、发通知要么全成要么全不成。
 * 早期这些逻辑散在 Controller 里，中间失败会留下「草稿删了但主表没更新」这类半完成状态。
 */
public interface AdminReviewService {

    /** 待审企业（含新入驻与资料修改草稿），已按创建时间倒序。 */
    List<Company> pendingCompanies();

    /** 待审岗位。 */
    List<Job> pendingJobs();

    /**
     * 审核企业。
     *
     * @param decision 只能传 APPROVED / REJECTED
     * @param reason   驳回时必填
     */
    void reviewCompany(Long companyId, String decision, String reason);

    /**
     * 审核岗位。
     *
     * @param decision 只能传 PUBLISHED / REJECTED
     * @param reason   驳回时必填
     */
    void reviewJob(Long jobId, String decision, String reason);
}
