package com.recruit_resume.service;

import com.recruit_resume.entity.StudentExperience;
import com.recruit_resume.entity.StudentProfile;
import com.recruit_resume.entity.StudentSkill;
import org.apache.poi.xwpf.usermodel.*;
import org.openxmlformats.schemas.wordprocessingml.x2006.main.*;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;

@Component
public class ResumeDocxBuilder {

    private static final String FONT_HEADING = "黑体";
    private static final String FONT_BODY = "宋体";
    private static final int FONT_SIZE_NAME = 36;       // 18pt
    private static final int FONT_SIZE_SECTION = 24;    // 12pt
    private static final int FONT_SIZE_BODY = 21;       // 10.5pt (五号)
    private static final int FONT_SIZE_SMALL = 18;      // 9pt

    public byte[] build(StudentProfile profile, List<StudentSkill> skills,
                        List<StudentExperience> experiences) throws IOException {
        try (XWPFDocument doc = new XWPFDocument()) {
            configurePage(doc);
            addHeader(doc, profile);
            addBasicInfo(doc, profile);
            addJobIntent(doc, profile);
            addEducation(doc, profile);
            addSkills(doc, skills);
            addExperiences(doc, experiences);
            addSelfIntro(doc, profile);
            try (ByteArrayOutputStream out = new ByteArrayOutputStream()) {
                doc.write(out);
                return out.toByteArray();
            }
        }
    }

    // ---- page setup ----

    private void configurePage(XWPFDocument doc) {
        CTSectPr sectPr = doc.getDocument().getBody().addNewSectPr();
        CTPageSz pageSz = sectPr.addNewPgSz();
        pageSz.setW(BigInteger.valueOf(11906)); // A4 width
        pageSz.setH(BigInteger.valueOf(16838)); // A4 height
        CTPageMar pageMar = sectPr.addNewPgMar();
        pageMar.setTop(BigInteger.valueOf(1440));
        pageMar.setBottom(BigInteger.valueOf(1440));
        pageMar.setLeft(BigInteger.valueOf(1800));
        pageMar.setRight(BigInteger.valueOf(1800));
    }

    // ---- header: name + contact ----

    private void addHeader(XWPFDocument doc, StudentProfile profile) {
        XWPFParagraph namePara = doc.createParagraph();
        setCenter(namePara);
        XWPFRun nameRun = namePara.createRun();
        setFont(nameRun, FONT_HEADING, FONT_SIZE_NAME, true);
        nameRun.setText(valueOr(profile.getRealName(), "未命名"));

        XWPFParagraph contactPara = doc.createParagraph();
        setCenter(contactPara);
        setSpacing(contactPara, 60, 80);
        XWPFRun contactRun = contactPara.createRun();
        setFont(contactRun, FONT_BODY, FONT_SIZE_SMALL, false);
        contactRun.setColor("666666");
        contactRun.setText(joinNonBlank(" | ",
                labeled("手机", profile.getPhone()),
                labeled("邮箱", profile.getEmail()),
                labeled("微信", profile.getWechat()),
                labeled("QQ", profile.getQq())));

        // thin separator
        XWPFParagraph sep = doc.createParagraph();
        setSpacing(sep, 0, 120);
        addBottomBorder(sep);
    }

    // ---- basic info ----

    private void addBasicInfo(XWPFDocument doc, StudentProfile profile) {
        addSectionHeading(doc, "基本信息");

        String[] labels = {"性别", "年龄", "籍贯", "政治面貌"};
        String[] values = {profile.getGender(), formatAge(profile.getAge()),
                profile.getHometown(), profile.getPoliticalStatus()};
        addLabelValueGrid(doc, labels, values);
    }

    // ---- job intent ----

    private void addJobIntent(XWPFDocument doc, StudentProfile profile) {
        addSectionHeading(doc, "求职意向");

        XWPFTable table = doc.createTable(1, 3);
        removeTableBorders(table);
        setCell(table.getRow(0).getCell(0), "期望岗位", profile.getExpectedPosition());
        setCell(table.getRow(0).getCell(1), "期望城市", profile.getExpectedCity());
        setCell(table.getRow(0).getCell(2), "期望薪资", profile.getExpectedSalary());
    }

    // ---- education ----

    private void addEducation(XWPFDocument doc, StudentProfile profile) {
        addSectionHeading(doc, "教育背景");

        XWPFTable table = doc.createTable(1, 3);
        removeTableBorders(table);
        setCell(table.getRow(0).getCell(0), "毕业院校", profile.getSchool());
        setCell(table.getRow(0).getCell(1), "专业", profile.getMajor());
        setCell(table.getRow(0).getCell(2), "学历", profile.getEducationLevel());

        XWPFTableRow row2 = table.createRow();
        setCell(row2.getCell(0), "GPA", profile.getGpa());
        setCell(row2.getCell(1), "毕业时间", formatGraduationDate(profile.getGraduationDate()));
        setCell(row2.getCell(2), "", "");
    }

    // ---- skills ----

    private void addSkills(XWPFDocument doc, List<StudentSkill> skills) {
        addSectionHeading(doc, "技能特长");

        if (skills == null || skills.isEmpty()) {
            addEmptyHint(doc);
            return;
        }

        XWPFTable table = doc.createTable(skills.size() + 1, 4);
        setTableBorders(table);
        String[] headers = {"技能名称", "技能类型", "熟练程度", "使用年限"};
        XWPFTableRow headerRow = table.getRow(0);
        for (int i = 0; i < headers.length; i++) {
            XWPFTableCell cell = headerRow.getCell(i);
            setCellShading(cell, "E8E8E8");
            setCellText(cell, headers[i], FONT_HEADING, FONT_SIZE_BODY, true);
        }
        for (int i = 0; i < skills.size(); i++) {
            StudentSkill skill = skills.get(i);
            XWPFTableRow row = table.getRow(i + 1);
            setCellText(row.getCell(0), skill.getSkillName(), FONT_BODY, FONT_SIZE_BODY, false);
            setCellText(row.getCell(1), valueOr(skill.getSkillType(), "-"), FONT_BODY, FONT_SIZE_BODY, false);
            setCellText(row.getCell(2), valueOr(skill.getProficiency(), "-"), FONT_BODY, FONT_SIZE_BODY, false);
            setCellText(row.getCell(3), formatYears(skill.getYears()), FONT_BODY, FONT_SIZE_BODY, false);
        }
    }

    // ---- experiences ----

    private void addExperiences(XWPFDocument doc, List<StudentExperience> experiences) {
        addSectionHeading(doc, "实践经历");

        if (experiences == null || experiences.isEmpty()) {
            addEmptyHint(doc);
            return;
        }

        for (int i = 0; i < experiences.size(); i++) {
            StudentExperience exp = experiences.get(i);
            XWPFParagraph titlePara = doc.createParagraph();
            if (i > 0) {
                setSpacing(titlePara, 120, 0);
            } else {
                setSpacing(titlePara, 0, 0);
            }
            XWPFRun titleRun = titlePara.createRun();
            setFont(titleRun, FONT_BODY, FONT_SIZE_BODY, true);
            titleRun.setText(joinNonBlank(" | ", exp.getTitle(), exp.getExperienceType()));

            if (StringUtils.hasText(exp.getTimeRange())) {
                XWPFRun timeRun = titlePara.createRun();
                setFont(timeRun, FONT_BODY, FONT_SIZE_SMALL, false);
                timeRun.setColor("888888");
                timeRun.setText("  " + exp.getTimeRange());
            }

            if (StringUtils.hasText(exp.getRoleName())) {
                XWPFParagraph rolePara = doc.createParagraph();
                setSpacing(rolePara, 20, 20);
                XWPFRun roleRun = rolePara.createRun();
                setFont(roleRun, FONT_BODY, FONT_SIZE_SMALL, false);
                roleRun.setColor("555555");
                roleRun.setText("担任：" + exp.getRoleName());
            }

            if (StringUtils.hasText(exp.getDescription())) {
                XWPFParagraph descPara = doc.createParagraph();
                setSpacing(descPara, 0, 80);
                XWPFRun descRun = descPara.createRun();
                setFont(descRun, FONT_BODY, FONT_SIZE_BODY, false);
                descRun.setText(exp.getDescription());
            }
        }
    }

    // ---- self-intro ----

    private void addSelfIntro(XWPFDocument doc, StudentProfile profile) {
        addSectionHeading(doc, "自我评价");
        if (StringUtils.hasText(profile.getSelfIntro())) {
            XWPFParagraph p = doc.createParagraph();
            setSpacing(p, 0, 0);
            XWPFRun run = p.createRun();
            setFont(run, FONT_BODY, FONT_SIZE_BODY, false);
            run.setText(profile.getSelfIntro());
        } else {
            addEmptyHint(doc);
        }
    }

    // ---- reusable helpers ----

    private void addSectionHeading(XWPFDocument doc, String title) {
        XWPFParagraph p = doc.createParagraph();
        setSpacing(p, 240, 60);
        addBottomBorder(p);
        XWPFRun run = p.createRun();
        setFont(run, FONT_HEADING, FONT_SIZE_SECTION, true);
        run.setText(title);
    }

    private void addEmptyHint(XWPFDocument doc) {
        XWPFParagraph p = doc.createParagraph();
        setSpacing(p, 0, 60);
        XWPFRun run = p.createRun();
        setFont(run, FONT_BODY, FONT_SIZE_SMALL, false);
        run.setColor("AAAAAA");
        run.setText("暂无数据");
    }

    private void addLabelValueGrid(XWPFDocument doc, String[] labels, String[] values) {
        XWPFTable table = doc.createTable(1, labels.length);
        removeTableBorders(table);
        XWPFTableRow row = table.getRow(0);
        for (int i = 0; i < labels.length; i++) {
            setCell(row.getCell(i), labels[i], values[i]);
        }
    }

    /** Set exactly 2 runs in the cell: label (gray, 9pt) + value (body, 10.5pt). */
    private void setCell(XWPFTableCell cell, String label, String value) {
        cell.removeParagraph(0);
        XWPFParagraph p = cell.addParagraph();
        XWPFRun labelRun = p.createRun();
        setFont(labelRun, FONT_BODY, FONT_SIZE_SMALL, false);
        labelRun.setColor("888888");
        labelRun.setText(label + "：");
        XWPFRun valueRun = p.createRun();
        setFont(valueRun, FONT_BODY, FONT_SIZE_BODY, false);
        valueRun.setText(valueOr(value, "未填写"));
    }

    private void setCellText(XWPFTableCell cell, String text, String font, int size, boolean bold) {
        cell.removeParagraph(0);
        XWPFParagraph p = cell.addParagraph();
        XWPFRun run = p.createRun();
        setFont(run, font, size, bold);
        run.setText(text);
    }

    private void setCellShading(XWPFTableCell cell, String hexColor) {
        CTShd shd = cell.getCTTc().addNewTcPr().addNewShd();
        shd.setFill(hexColor);
        shd.setVal(STShd.CLEAR);
    }

    private void removeTableBorders(XWPFTable table) {
        CTTblBorders borders = table.getCTTbl().addNewTblPr().addNewTblBorders();
        borders.addNewTop().setVal(STBorder.NONE);
        borders.addNewBottom().setVal(STBorder.NONE);
        borders.addNewLeft().setVal(STBorder.NONE);
        borders.addNewRight().setVal(STBorder.NONE);
        borders.addNewInsideH().setVal(STBorder.NONE);
        borders.addNewInsideV().setVal(STBorder.NONE);
    }

    private void setTableBorders(XWPFTable table) {
        CTTblBorders borders = table.getCTTbl().addNewTblPr().addNewTblBorders();
        setBorder(borders.addNewTop());
        setBorder(borders.addNewBottom());
        setBorder(borders.addNewLeft());
        setBorder(borders.addNewRight());
        setBorder(borders.addNewInsideH());
        setBorder(borders.addNewInsideV());
    }

    private void setBorder(CTBorder border) {
        border.setVal(STBorder.SINGLE);
        border.setSz(BigInteger.valueOf(4));
        border.setColor("CCCCCC");
    }

    // ---- font helpers ----

    private void setFont(XWPFRun run, String fontName, int fontSizeHalfPt, boolean bold) {
        run.setFontFamily(fontName);
        run.setFontSize(fontSizeHalfPt);
        run.setBold(bold);
        // setFontFamily already creates an rFonts element — set east-asia on it
        CTRPr rPr = run.getCTR().getRPr();
        if (rPr.sizeOfRFontsArray() > 0) {
            rPr.getRFontsArray(0).setEastAsia(fontName);
        }
    }

    // ---- paragraph helpers ----

    private void setCenter(XWPFParagraph p) {
        p.setAlignment(ParagraphAlignment.CENTER);
    }

    private void setSpacing(XWPFParagraph p, int beforeTwips, int afterTwips) {
        p.setSpacingBefore(beforeTwips);
        p.setSpacingAfter(afterTwips);
    }

    private void addBottomBorder(XWPFParagraph p) {
        CTPPr pPr = p.getCTP().isSetPPr() ? p.getCTP().getPPr() : p.getCTP().addNewPPr();
        CTPBdr borders = pPr.addNewPBdr();
        CTBorder bottom = borders.addNewBottom();
        bottom.setVal(STBorder.SINGLE);
        bottom.setSz(BigInteger.valueOf(4));
        bottom.setColor("AAAAAA");
        bottom.setSpace(BigInteger.valueOf(4));
    }

    // ---- data helpers ----

    private String joinNonBlank(String separator, String... values) {
        StringBuilder sb = new StringBuilder();
        for (String v : values) {
            if (StringUtils.hasText(v)) {
                if (!sb.isEmpty()) {
                    sb.append(separator);
                }
                sb.append(v);
            }
        }
        return sb.isEmpty() ? "" : sb.toString();
    }

    private String labeled(String label, String value) {
        if (!StringUtils.hasText(value)) {
            return "";
        }
        return label + "：" + value;
    }

    private String valueOr(String value, String fallback) {
        return StringUtils.hasText(value) ? value : fallback;
    }

    private String formatAge(Integer age) {
        return age != null ? age + "岁" : "";
    }

    private String formatGraduationDate(LocalDate date) {
        if (date == null) return "";
        return date.format(DateTimeFormatter.ofPattern("yyyy年M月"));
    }

    private String formatYears(java.math.BigDecimal years) {
        if (years == null) return "-";
        return years.stripTrailingZeros().toPlainString() + "年";
    }
}
