package com.recruit_resume.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class ResumeSchemaInitializer implements ApplicationRunner {

    private final JdbcTemplate jdbcTemplate;

    public ResumeSchemaInitializer(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    public void run(ApplicationArguments args) {
        createResumeTemplateTable();
        createResumeSnapshotTable();
        allowTemplateCoverBusinessType();
        seedDefaultTemplates();
    }

    private void createResumeTemplateTable() {
        jdbcTemplate.execute("""
                CREATE TABLE IF NOT EXISTS resume_template (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '模板ID',
                    template_name VARCHAR(100) NOT NULL COMMENT '模板名称',
                    template_code VARCHAR(50) NOT NULL COMMENT '代码模板标识',
                    cover_file_id BIGINT COMMENT '模板封面文件ID',
                    description VARCHAR(500) COMMENT '模板说明',
                    enabled TINYINT NOT NULL DEFAULT 1 COMMENT '是否启用',
                    sort_order INT NOT NULL DEFAULT 0 COMMENT '排序',
                    version INT NOT NULL DEFAULT 1 COMMENT '模板版本',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    CONSTRAINT uk_resume_template_code UNIQUE (template_code),
                    CONSTRAINT fk_resume_template_cover FOREIGN KEY (cover_file_id) REFERENCES file_resource(id),
                    CONSTRAINT chk_resume_template_enabled CHECK (enabled IN (0, 1)),
                    INDEX idx_resume_template_enabled_sort (enabled, sort_order)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='简历模板表'
                """);
    }

    private void createResumeSnapshotTable() {
        jdbcTemplate.execute("""
                CREATE TABLE IF NOT EXISTS resume_snapshot (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '快照ID',
                    resume_id BIGINT NOT NULL COMMENT '关联简历ID',
                    student_id BIGINT NOT NULL COMMENT '学生资料ID',
                    template_id BIGINT NOT NULL COMMENT '模板ID',
                    snapshot_json JSON NOT NULL COMMENT '生成时的数据快照',
                    html_content MEDIUMTEXT NOT NULL COMMENT '生成PDF使用的最终HTML',
                    generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
                    CONSTRAINT uk_resume_snapshot_resume UNIQUE (resume_id),
                    CONSTRAINT fk_resume_snapshot_resume FOREIGN KEY (resume_id) REFERENCES resume(id) ON DELETE CASCADE,
                    CONSTRAINT fk_resume_snapshot_student FOREIGN KEY (student_id) REFERENCES student_profile(id) ON DELETE CASCADE,
                    CONSTRAINT fk_resume_snapshot_template FOREIGN KEY (template_id) REFERENCES resume_template(id),
                    INDEX idx_resume_snapshot_student (student_id),
                    INDEX idx_resume_snapshot_template (template_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='简历生成快照表'
                """);
    }

    private void allowTemplateCoverBusinessType() {
        try {
            jdbcTemplate.execute("ALTER TABLE file_resource DROP CHECK chk_file_resource_business_type");
        } catch (RuntimeException ex) {
            log.debug("Skip dropping file_resource business type check: {}", ex.getMessage());
        }
        try {
            jdbcTemplate.execute("""
                    ALTER TABLE file_resource
                    ADD CONSTRAINT chk_file_resource_business_type
                    CHECK (business_type IN ('RESUME', 'AVATAR', 'LOGO', 'CERTIFICATE', 'TEMPLATE_COVER'))
                    """);
        } catch (RuntimeException ex) {
            log.debug("Skip adding file_resource business type check: {}", ex.getMessage());
        }
    }

    private void seedDefaultTemplates() {
        insertTemplateIfMissing(
                "经典专业版",
                "classic",
                "适合大多数校园招聘投递，信息完整、结构清晰",
                10
        );
        insertTemplateIfMissing(
                "紧凑校园版",
                "compact",
                "适合经历较多的应届生，版面紧凑、重点明确",
                20
        );
        insertTemplateIfMissing(
                "项目突出版",
                "project",
                "突出项目与技能成果，适合技术岗位投递",
                30
        );
    }

    private void insertTemplateIfMissing(String name, String code, String description, int sortOrder) {
        Integer count = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM resume_template WHERE template_code = ?",
                Integer.class,
                code
        );
        if (count != null && count > 0) {
            return;
        }
        jdbcTemplate.update("""
                INSERT INTO resume_template
                    (template_name, template_code, description, enabled, sort_order, version)
                VALUES (?, ?, ?, 1, ?, 1)
                """, name, code, description, sortOrder);
    }
}
