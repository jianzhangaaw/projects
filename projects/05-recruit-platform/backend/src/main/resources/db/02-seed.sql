-- 演示种子数据：三个角色账号，密码统一 Demo@1234
-- 由 _seed.py 生成，BCrypt 哈希每次不同但都对应同一密码
SET NAMES utf8mb4;
USE recruit_resume;

INSERT INTO user_account (id, username, password, email, phone, role, status) VALUES
(1, 'admin', '$2a$10$uI/WHCV90LEGx6BXD.2TM.ViNSEeN4s1G.It/i9c35N0aWX6AZ0j6', 'admin@example.com', NULL, 'ADMIN', 'ENABLED'),
(2, 'student01', '$2a$10$HUKiDGdAFvUCNvMH1eZg9.xps.a0xlmt4HOIYCiXA6Hoojlrgn1mO', 'student01@example.com', '13800000001', 'STUDENT', 'ENABLED'),
(3, 'company01', '$2a$10$k0q4qvb9f2F/ZKbwtzuscuf3XQ.ljAlyowerQ1QgUa8.eaj0TZUEC', 'company01@example.com', '13800000002', 'COMPANY', 'ENABLED')
ON DUPLICATE KEY UPDATE password = VALUES(password), role = VALUES(role), status = VALUES(status);

INSERT INTO student_profile
  (id, user_id, real_name, gender, age, hometown, political_status, phone, email,
   school, major, education_level, gpa, graduation_date,
   expected_position, expected_city, expected_salary, self_intro)
VALUES
  (1, 2, '夏遂冬', '男', 22, '江西南昌', '共青团员', '13800000001', 'student01@example.com',
   '南昌大学', '软件工程', '本科', '3.7/4.0', '2027-06-30',
   'Java 后端开发工程师', '南昌', '10-15K',
   '软件工程本科在读，熟悉 Java / Spring Boot / MySQL / Vue3，做过招聘平台、数据挖掘与小程序项目。')
ON DUPLICATE KEY UPDATE real_name = VALUES(real_name), school = VALUES(school), major = VALUES(major);

INSERT INTO student_skill (id, student_id, skill_name, skill_type, proficiency, years) VALUES
  (1, 1, 'Java', '编程语言', '精通', 2.0),
  (2, 1, 'Spring Boot', '后端框架', '精通', 1.0),
  (3, 1, 'MySQL', '数据库', '掌握', 1.5),
  (4, 1, 'Vue3', '前端框架', '掌握', 1.0),
  (5, 1, 'Python', '编程语言', '掌握', 2.0)
ON DUPLICATE KEY UPDATE skill_name = VALUES(skill_name);

INSERT INTO company
  (id, user_id, company_name, industry, company_size, contact_name, contact_phone, description, review_status)
VALUES
  (1, 3, '星海科技（演示企业）', '互联网/软件', '100-499人', '王经理', '13800000002',
   '一家虚构的演示企业，用于作品集里展示企业的岗位发布与简历筛选流程。', 'APPROVED')
ON DUPLICATE KEY UPDATE company_name = VALUES(company_name), review_status = VALUES(review_status);

INSERT INTO job
  (id, company_id, job_name, job_type, city, salary_range, education_requirement,
   major_requirement, skill_requirement, description, status, view_count)
VALUES
  (1, 1, 'Java 后端开发工程师', '全职', '南昌', '10-15K', '本科',
   '计算机相关专业', 'Java / Spring Boot / MySQL / MyBatis',
   '负责招聘平台后端接口开发，参与需求评审与数据库设计。', 'PUBLISHED', 12),
  (2, 1, '前端开发工程师（Vue3）', '全职', '南昌', '9-14K', '本科',
   '计算机相关专业', 'Vue3 / TypeScript / Element Plus',
   '负责企业端与学生端页面开发，配合后端联调。', 'PUBLISHED', 8),
  (3, 1, '数据分析实习生', '实习', '远程', '150-200/天', '本科',
   '统计/计算机相关专业', 'Python / pandas / SQL',
   '协助整理招聘数据，产出岗位与投递的周报。', 'PUBLISHED', 5)
ON DUPLICATE KEY UPDATE job_name = VALUES(job_name), status = VALUES(status);
