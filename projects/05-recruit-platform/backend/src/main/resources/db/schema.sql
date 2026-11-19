-- 容器里由 docker-entrypoint 用 mysql 客户端执行，务必先声明字符集，
-- 否则 CHECK 约束里的中文字面量会被当成 latin1，之后任何中文取值都通不过校验。
SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS recruit_resume DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE recruit_resume;

CREATE TABLE IF NOT EXISTS user_account (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '账号ID',
    username VARCHAR(50) NOT NULL COMMENT '用户名',
    password VARCHAR(100) NOT NULL COMMENT '加密后的密码',
    email VARCHAR(100) COMMENT '邮箱',
    phone VARCHAR(20) COMMENT '手机号',
    role VARCHAR(20) NOT NULL COMMENT '角色: STUDENT/COMPANY/ADMIN',
    status VARCHAR(20) NOT NULL DEFAULT 'ENABLED' COMMENT '账号状态: ENABLED/DISABLED',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT uk_user_account_username UNIQUE (username),
    CONSTRAINT uk_user_account_email UNIQUE (email),
    CONSTRAINT uk_user_account_phone UNIQUE (phone),
    CONSTRAINT chk_user_account_role CHECK (role IN ('STUDENT', 'COMPANY', 'ADMIN')),
    CONSTRAINT chk_user_account_status CHECK (status IN ('ENABLED', 'DISABLED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='统一用户账号表';

CREATE TABLE IF NOT EXISTS file_resource (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '文件ID',
    uploader_id BIGINT NOT NULL COMMENT '上传用户ID',
    file_name VARCHAR(255) NOT NULL COMMENT '原始文件名',
    file_type VARCHAR(50) NOT NULL COMMENT '文件类型',
    file_url VARCHAR(255) NOT NULL COMMENT '文件访问地址或存储路径',
    file_size BIGINT NOT NULL DEFAULT 0 COMMENT '文件大小',
    business_type VARCHAR(50) NOT NULL COMMENT '业务类型: RESUME/AVATAR/LOGO/CERTIFICATE/TEMPLATE_COVER',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_file_resource_uploader FOREIGN KEY (uploader_id) REFERENCES user_account(id),
    CONSTRAINT chk_file_resource_business_type CHECK (business_type IN ('RESUME', 'AVATAR', 'LOGO', 'CERTIFICATE', 'TEMPLATE_COVER')),
    INDEX idx_file_resource_uploader (uploader_id),
    INDEX idx_file_resource_business_type (business_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文件资源表';

CREATE TABLE IF NOT EXISTS student_profile (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '学生资料ID',
    user_id BIGINT NOT NULL COMMENT '关联账号ID',
    real_name VARCHAR(50) COMMENT '真实姓名',
    gender VARCHAR(10) COMMENT '性别',
    age INT COMMENT '年龄',
    hometown VARCHAR(100) COMMENT '籍贯',
    political_status VARCHAR(50) COMMENT '政治面貌',
    phone VARCHAR(20) COMMENT '手机号',
    email VARCHAR(100) COMMENT '邮箱',
    wechat VARCHAR(50) COMMENT '微信',
    qq VARCHAR(30) COMMENT 'QQ',
    school VARCHAR(100) COMMENT '学校',
    major VARCHAR(100) COMMENT '专业',
    education_level VARCHAR(50) COMMENT '学历',
    gpa VARCHAR(20) COMMENT 'GPA',
    graduation_date DATE COMMENT '毕业时间',
    expected_position VARCHAR(100) COMMENT '期望岗位',
    expected_city VARCHAR(100) COMMENT '期望城市',
    expected_salary VARCHAR(50) COMMENT '期望薪资',
    self_intro TEXT COMMENT '个人简介',
    avatar_file_id BIGINT COMMENT '头像文件ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT uk_student_profile_user UNIQUE (user_id),
    CONSTRAINT fk_student_profile_user FOREIGN KEY (user_id) REFERENCES user_account(id),
    CONSTRAINT fk_student_profile_avatar FOREIGN KEY (avatar_file_id) REFERENCES file_resource(id),
    INDEX idx_student_profile_school_major (school, major),
    INDEX idx_student_profile_graduation_date (graduation_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生个人资料表';

CREATE TABLE IF NOT EXISTS student_skill (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '技能ID',
    student_id BIGINT NOT NULL COMMENT '学生资料ID',
    skill_name VARCHAR(50) NOT NULL COMMENT '技能名称',
    skill_type VARCHAR(50) COMMENT '技能分类',
    proficiency VARCHAR(20) COMMENT '熟练度',
    years DECIMAL(3,1) DEFAULT 0 COMMENT '使用年限',
    file_id BIGINT COMMENT '技能证书文件ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_student_skill_student FOREIGN KEY (student_id) REFERENCES student_profile(id) ON DELETE CASCADE,
    CONSTRAINT fk_student_skill_file FOREIGN KEY (file_id) REFERENCES file_resource(id),
    CONSTRAINT chk_student_skill_proficiency CHECK (proficiency IS NULL OR proficiency IN ('了解', '熟悉', '掌握', '精通')),
    INDEX idx_student_skill_student (student_id),
    INDEX idx_student_skill_name (skill_name),
    INDEX idx_student_skill_type (skill_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生技能能力表';

CREATE TABLE IF NOT EXISTS student_experience (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '经历ID',
    student_id BIGINT NOT NULL COMMENT '学生资料ID',
    experience_type VARCHAR(30) NOT NULL COMMENT '经历类型: PROJECT/INTERNSHIP/COMPETITION_HONOR',
    title VARCHAR(100) NOT NULL COMMENT '经历标题',
    time_range VARCHAR(100) COMMENT '时间范围',
    role_name VARCHAR(100) COMMENT '角色或职务',
    description TEXT COMMENT '经历描述',
    file_id BIGINT COMMENT '证明材料文件ID',
    sort_order INT NOT NULL DEFAULT 0 COMMENT '排序',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_student_experience_student FOREIGN KEY (student_id) REFERENCES student_profile(id) ON DELETE CASCADE,
    CONSTRAINT fk_student_experience_file FOREIGN KEY (file_id) REFERENCES file_resource(id),
    CONSTRAINT chk_student_experience_type CHECK (experience_type IN ('PROJECT', 'INTERNSHIP', 'COMPETITION_HONOR')),
    INDEX idx_student_experience_student (student_id),
    INDEX idx_student_experience_type (experience_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生经历表';

CREATE TABLE IF NOT EXISTS resume (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '简历ID',
    student_id BIGINT NOT NULL COMMENT '学生资料ID',
    resume_name VARCHAR(100) NOT NULL COMMENT '简历名称',
    resume_type VARCHAR(20) NOT NULL COMMENT '简历类型: ONLINE/UPLOAD',
    target_position VARCHAR(100) COMMENT '目标岗位',
    file_id BIGINT COMMENT 'PDF文件ID',
    school VARCHAR(100) COMMENT '搜索索引: 学校',
    major VARCHAR(100) COMMENT '搜索索引: 专业',
    education_level VARCHAR(50) COMMENT '搜索索引: 学历',
    graduation_date DATE COMMENT '搜索索引: 毕业时间',
    skill_tags VARCHAR(255) COMMENT '搜索索引: 技能标签',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_resume_student FOREIGN KEY (student_id) REFERENCES student_profile(id) ON DELETE CASCADE,
    CONSTRAINT fk_resume_file FOREIGN KEY (file_id) REFERENCES file_resource(id),
    CONSTRAINT chk_resume_type CHECK (resume_type IN ('ONLINE', 'UPLOAD')),
    INDEX idx_resume_student (student_id),
    INDEX idx_resume_type (resume_type),
    INDEX idx_resume_search (school, major, education_level, graduation_date),
    INDEX idx_resume_target_position (target_position)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='简历表';

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='简历模板表';

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='简历生成快照表';

INSERT INTO resume_template (template_name, template_code, description, enabled, sort_order, version)
SELECT '经典专业版', 'classic', '适合大多数校园招聘投递，信息完整、结构清晰', 1, 10, 1
WHERE NOT EXISTS (SELECT 1 FROM resume_template WHERE template_code = 'classic');

INSERT INTO resume_template (template_name, template_code, description, enabled, sort_order, version)
SELECT '紧凑校园版', 'compact', '适合经历较多的应届生，版面紧凑、重点明确', 1, 20, 1
WHERE NOT EXISTS (SELECT 1 FROM resume_template WHERE template_code = 'compact');

INSERT INTO resume_template (template_name, template_code, description, enabled, sort_order, version)
SELECT '项目突出版', 'project', '突出项目与技能成果，适合技术岗位投递', 1, 30, 1
WHERE NOT EXISTS (SELECT 1 FROM resume_template WHERE template_code = 'project');

CREATE TABLE IF NOT EXISTS company (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '企业ID',
    user_id BIGINT NOT NULL COMMENT '关联账号ID',
    company_name VARCHAR(100) NOT NULL COMMENT '企业名称',
    industry VARCHAR(100) COMMENT '行业',
    company_size VARCHAR(50) COMMENT '规模',
    contact_name VARCHAR(50) COMMENT '联系人',
    contact_phone VARCHAR(20) COMMENT '联系电话',
    description TEXT COMMENT '企业简介',
    logo_file_id BIGINT COMMENT '企业Logo文件ID',
    review_status VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT '入驻审核状态',
    review_reason VARCHAR(255) COMMENT '审核原因',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT uk_company_user UNIQUE (user_id),
    CONSTRAINT fk_company_user FOREIGN KEY (user_id) REFERENCES user_account(id),
    CONSTRAINT fk_company_logo FOREIGN KEY (logo_file_id) REFERENCES file_resource(id),
    CONSTRAINT chk_company_review_status CHECK (review_status IN ('PENDING', 'APPROVED', 'REJECTED')),
    INDEX idx_company_name (company_name),
    INDEX idx_company_review_status (review_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='企业信息表';

-- 企业资料修改草稿：企业提交修改后先进草稿表，管理员审核通过才写回 company。
-- CompanyController / AdminReviewController 都依赖它，缺表会让"企业资料修改"与"入驻审核"直接 500。
CREATE TABLE IF NOT EXISTS company_draft (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '草稿ID',
    company_id BIGINT NOT NULL COMMENT '关联企业ID',
    company_name VARCHAR(100) COMMENT '企业名称',
    industry VARCHAR(100) COMMENT '行业',
    company_size VARCHAR(50) COMMENT '规模',
    contact_name VARCHAR(50) COMMENT '联系人',
    contact_phone VARCHAR(20) COMMENT '联系电话',
    description TEXT COMMENT '企业简介',
    logo_file_id BIGINT COMMENT '企业Logo文件ID',
    review_status VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT '审核状态',
    review_reason VARCHAR(255) COMMENT '审核原因',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_company_draft_company FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE,
    CONSTRAINT fk_company_draft_logo FOREIGN KEY (logo_file_id) REFERENCES file_resource(id),
    CONSTRAINT chk_company_draft_status CHECK (review_status IN ('PENDING', 'APPROVED', 'REJECTED')),
    INDEX idx_company_draft_company (company_id),
    INDEX idx_company_draft_status (review_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='企业资料修改草稿表';

CREATE TABLE IF NOT EXISTS job (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '岗位ID',
    company_id BIGINT NOT NULL COMMENT '企业ID',
    job_name VARCHAR(100) NOT NULL COMMENT '岗位名称',
    job_type VARCHAR(50) COMMENT '岗位类型',
    city VARCHAR(100) COMMENT '工作城市',
    salary_range VARCHAR(50) COMMENT '薪资范围',
    education_requirement VARCHAR(50) COMMENT '学历要求',
    major_requirement VARCHAR(100) COMMENT '专业要求',
    skill_requirement VARCHAR(255) COMMENT '技能要求',
    description TEXT COMMENT '岗位描述',
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT' COMMENT '岗位状态',
    review_reason VARCHAR(255) COMMENT '审核原因',
    view_count INT NOT NULL DEFAULT 0 COMMENT '浏览量',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_job_company FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE,
    CONSTRAINT chk_job_status CHECK (status IN ('DRAFT', 'PENDING', 'PUBLISHED', 'OFFLINE', 'REJECTED')),
    INDEX idx_job_company (company_id),
    INDEX idx_job_status (status),
    INDEX idx_job_city_type (city, job_type),
    INDEX idx_job_name (job_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='岗位表';

CREATE TABLE IF NOT EXISTS job_application (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '投递ID',
    job_id BIGINT NOT NULL COMMENT '岗位ID',
    company_id BIGINT NOT NULL COMMENT '企业ID',
    student_id BIGINT NOT NULL COMMENT '学生资料ID',
    resume_id BIGINT NOT NULL COMMENT '投递使用的简历ID',
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT '投递处理状态',
    remark VARCHAR(255) COMMENT '企业备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_job_application_job FOREIGN KEY (job_id) REFERENCES job(id),
    CONSTRAINT fk_job_application_company FOREIGN KEY (company_id) REFERENCES company(id),
    CONSTRAINT fk_job_application_student FOREIGN KEY (student_id) REFERENCES student_profile(id),
    CONSTRAINT fk_job_application_resume FOREIGN KEY (resume_id) REFERENCES resume(id),
    CONSTRAINT uk_job_application_job_student UNIQUE (job_id, student_id),
    CONSTRAINT chk_job_application_status CHECK (status IN ('PENDING', 'PASSED', 'REJECTED')),
    INDEX idx_job_application_company_status (company_id, status),
    INDEX idx_job_application_student_status (student_id, status),
    INDEX idx_job_application_resume (resume_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='岗位投递表';

CREATE TABLE IF NOT EXISTS notification (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '通知ID',
    receiver_id BIGINT NOT NULL COMMENT '接收用户ID',
    title VARCHAR(100) NOT NULL COMMENT '标题',
    content VARCHAR(500) NOT NULL COMMENT '通知内容',
    type VARCHAR(50) NOT NULL COMMENT '通知类型: APPLICATION/REVIEW',
    is_read TINYINT NOT NULL DEFAULT 0 COMMENT '是否已读',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_notification_receiver FOREIGN KEY (receiver_id) REFERENCES user_account(id) ON DELETE CASCADE,
    CONSTRAINT chk_notification_type CHECK (type IN ('APPLICATION', 'REVIEW')),
    CONSTRAINT chk_notification_is_read CHECK (is_read IN (0, 1)),
    INDEX idx_notification_receiver_read (receiver_id, is_read),
    INDEX idx_notification_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统通知表';
