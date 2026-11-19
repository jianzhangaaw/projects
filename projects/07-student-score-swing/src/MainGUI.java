import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.List;

/**
 * 主程序类，提供图形用户界面
 */
public class MainGUI extends JFrame {
    private StudentManager manager = new StudentManager();
    private JTextArea outputArea;

    public MainGUI() {
        setTitle("学生成绩管理系统");
        setSize(800, 600);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        // 创建菜单栏
        createMenuBar();

        // 创建主面板
        JPanel mainPanel = new JPanel(new BorderLayout());

        // 创建输出区域
        outputArea = new JTextArea();
        outputArea.setEditable(false);
        JScrollPane scrollPane = new JScrollPane(outputArea);
        mainPanel.add(scrollPane, BorderLayout.CENTER);

        // 添加主面板
        add(mainPanel);

        // 加载学生数据
        manager.loadStudents();
        appendText("学生成绩管理系统已启动，共加载 " + manager.getTotalCount() + " 名学生数据。\n");
    }

    // 创建菜单栏
    private void createMenuBar() {
        JMenuBar menuBar = new JMenuBar();

        // 文件菜单
        JMenu fileMenu = new JMenu("文件");
        JMenuItem exitItem = new JMenuItem("退出");
        exitItem.addActionListener(e -> System.exit(0));
        fileMenu.add(exitItem);
        menuBar.add(fileMenu);

        // 学生管理菜单
        JMenu studentMenu = new JMenu("学生管理");
        JMenuItem addItem = new JMenuItem("添加学生");
        addItem.addActionListener(e -> addStudentDialog());
        studentMenu.add(addItem);

        JMenuItem updateItem = new JMenuItem("修改学生");
        updateItem.addActionListener(e -> updateStudentDialog());
        studentMenu.add(updateItem);

        JMenuItem deleteItem = new JMenuItem("删除学生");
        deleteItem.addActionListener(e -> deleteStudentDialog());
        studentMenu.add(deleteItem);

        JMenuItem viewAllItem = new JMenuItem("查看所有学生");
        viewAllItem.addActionListener(e -> viewAllStudents());
        studentMenu.add(viewAllItem);
        menuBar.add(studentMenu);

        // 查询菜单
        JMenu searchMenu = new JMenu("查询");
        JMenuItem searchClassItem = new JMenuItem("按班级查询");
        searchClassItem.addActionListener(e -> searchByClassDialog());
        searchMenu.add(searchClassItem);

        JMenuItem searchNameItem = new JMenuItem("按姓名查询");
        searchNameItem.addActionListener(e -> searchByNameDialog());
        searchMenu.add(searchNameItem);

        JMenuItem searchIdItem = new JMenuItem("按学号查询");
        searchIdItem.addActionListener(e -> searchByIdDialog());
        searchMenu.add(searchIdItem);
        menuBar.add(searchMenu);

        // 排序菜单
        JMenu sortMenu = new JMenu("排序");
        JMenuItem sortChineseItem = new JMenuItem("按语文成绩排序");
        sortChineseItem.addActionListener(e -> sortBySubject("chinese"));
        sortMenu.add(sortChineseItem);

        JMenuItem sortMathItem = new JMenuItem("按数学成绩排序");
        sortMathItem.addActionListener(e -> sortBySubject("math"));
        sortMenu.add(sortMathItem);

        JMenuItem sortEnglishItem = new JMenuItem("按英语成绩排序");
        sortEnglishItem.addActionListener(e -> sortBySubject("english"));
        sortMenu.add(sortEnglishItem);

        JMenuItem sortTotalItem = new JMenuItem("按总成绩排序");
        sortTotalItem.addActionListener(e -> sortByTotalScore());
        sortMenu.add(sortTotalItem);

        JMenuItem sortIdItem = new JMenuItem("按学号排序");
        sortIdItem.addActionListener(e -> sortById());
        sortMenu.add(sortIdItem);
        menuBar.add(sortMenu);

        // 统计菜单
        JMenu statsMenu = new JMenu("统计");
        JMenuItem undergradCountItem = new JMenuItem("本科生人数");
        undergradCountItem.addActionListener(e -> viewUndergraduateCount());
        statsMenu.add(undergradCountItem);

        JMenuItem gradCountItem = new JMenuItem("研究生人数");
        gradCountItem.addActionListener(e -> viewGraduateCount());
        statsMenu.add(gradCountItem);

        JMenuItem totalCountItem = new JMenuItem("学生总人数");
        totalCountItem.addActionListener(e -> viewTotalCount());
        statsMenu.add(totalCountItem);
        menuBar.add(statsMenu);

        // 关于菜单
        JMenu aboutMenu = new JMenu("关于");
        JMenuItem aboutItem = new JMenuItem("关于系统");
        aboutItem.addActionListener(e -> showAboutDialog());
        aboutMenu.add(aboutItem);
        menuBar.add(aboutMenu);

        setJMenuBar(menuBar);
    }

    // 添加学生对话框
    private void addStudentDialog() {
        JDialog dialog = new JDialog(this, "添加学生", true);
        dialog.setSize(400, 350);
        dialog.setLocationRelativeTo(this);
        dialog.setLayout(new BorderLayout());

        JPanel panel = new JPanel(new GridLayout(7, 2, 10, 10));
        panel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        JTextField idField = new JTextField();
        JTextField nameField = new JTextField();
        JTextField classField = new JTextField();
        JTextField chineseField = new JTextField();
        JTextField mathField = new JTextField();
        JTextField englishField = new JTextField();
        JComboBox<String> typeComboBox = new JComboBox<>(new String[]{"本科生", "研究生"});

        panel.add(new JLabel("学号:"));
        panel.add(idField);
        panel.add(new JLabel("姓名:"));
        panel.add(nameField);
        panel.add(new JLabel("班级:"));
        panel.add(classField);
        panel.add(new JLabel("学生类型:"));
        panel.add(typeComboBox);
        panel.add(new JLabel("语文成绩:"));
        panel.add(chineseField);
        panel.add(new JLabel("数学成绩:"));
        panel.add(mathField);
        panel.add(new JLabel("英语成绩:"));
        panel.add(englishField);

        JButton okButton = new JButton("确定");
        JButton cancelButton = new JButton("取消");

        JPanel buttonPanel = new JPanel();
        buttonPanel.add(okButton);
        buttonPanel.add(cancelButton);

        dialog.add(panel, BorderLayout.CENTER);
        dialog.add(buttonPanel, BorderLayout.SOUTH);

        okButton.addActionListener(e -> {
            try {
                String studentId = idField.getText().trim();
                String name = nameField.getText().trim();
                String className = classField.getText().trim();
                double chinese = Double.parseDouble(chineseField.getText());
                double math = Double.parseDouble(mathField.getText());
                double english = Double.parseDouble(englishField.getText());
                boolean isUndergrad = typeComboBox.getSelectedIndex() == 0;

                if (studentId.isEmpty() || name.isEmpty() || className.isEmpty()) {
                    JOptionPane.showMessageDialog(dialog, "学号、姓名和班级不能为空！", "输入错误", JOptionPane.ERROR_MESSAGE);
                    return;
                }

                Student student;
                if (isUndergrad) {
                    student = new UndergraduateStudent(studentId, name, className, chinese, math, english);
                } else {
                    student = new GraduateStudent(studentId, name, className, chinese, math, english);
                }

                manager.addStudent(student);
                appendText("成功添加学生: " + name + " (" + studentId + ")\n");
                dialog.dispose();
            } catch (NumberFormatException ex) {
                JOptionPane.showMessageDialog(dialog, "成绩必须为数字！", "输入错误", JOptionPane.ERROR_MESSAGE);
            }
        });

        cancelButton.addActionListener(e -> dialog.dispose());

        dialog.setVisible(true);
    }

    // 修改学生对话框
    private void updateStudentDialog() {
        String studentId = JOptionPane.showInputDialog(this, "请输入要修改的学生学号:");
        if (studentId == null || studentId.trim().isEmpty()) return;

        Student student = manager.getStudentById(studentId);
        if (student == null) {
            JOptionPane.showMessageDialog(this, "未找到该学生！", "查找结果", JOptionPane.INFORMATION_MESSAGE);
            return;
        }

        JDialog dialog = new JDialog(this, "修改学生信息", true);
        dialog.setSize(400, 350);
        dialog.setLocationRelativeTo(this);
        dialog.setLayout(new BorderLayout());

        JPanel panel = new JPanel(new GridLayout(7, 2, 10, 10));
        panel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        JTextField idField = new JTextField(student.getStudentId());
        JTextField nameField = new JTextField(student.getName());
        JTextField classField = new JTextField(student.getClassName());
        JTextField chineseField = new JTextField(String.valueOf(student.getChinese()));
        JTextField mathField = new JTextField(String.valueOf(student.getMath()));
        JTextField englishField = new JTextField(String.valueOf(student.getEnglish()));
        JComboBox<String> typeComboBox = new JComboBox<>(new String[]{"本科生", "研究生"});

        if (student instanceof UndergraduateStudent) {
            typeComboBox.setSelectedIndex(0);
        } else {
            typeComboBox.setSelectedIndex(1);
        }

        idField.setEditable(false); // 学号不可修改

        panel.add(new JLabel("学号:"));
        panel.add(idField);
        panel.add(new JLabel("姓名:"));
        panel.add(nameField);
        panel.add(new JLabel("班级:"));
        panel.add(classField);
        panel.add(new JLabel("学生类型:"));
        panel.add(typeComboBox);
        panel.add(new JLabel("语文成绩:"));
        panel.add(chineseField);
        panel.add(new JLabel("数学成绩:"));
        panel.add(mathField);
        panel.add(new JLabel("英语成绩:"));
        panel.add(englishField);

        JButton okButton = new JButton("确定");
        JButton cancelButton = new JButton("取消");

        JPanel buttonPanel = new JPanel();
        buttonPanel.add(okButton);
        buttonPanel.add(cancelButton);

        dialog.add(panel, BorderLayout.CENTER);
        dialog.add(buttonPanel, BorderLayout.SOUTH);

        okButton.addActionListener(e -> {
            try {
                String name = nameField.getText().trim();
                String className = classField.getText().trim();
                double chinese = Double.parseDouble(chineseField.getText());
                double math = Double.parseDouble(mathField.getText());
                double english = Double.parseDouble(englishField.getText());
                boolean isUndergrad = typeComboBox.getSelectedIndex() == 0;

                if (name.isEmpty() || className.isEmpty()) {
                    JOptionPane.showMessageDialog(dialog, "姓名和班级不能为空！", "输入错误", JOptionPane.ERROR_MESSAGE);
                    return;
                }

                Student updatedStudent;
                if (isUndergrad) {
                    updatedStudent = new UndergraduateStudent(studentId, name, className, chinese, math, english);
                } else {
                    updatedStudent = new GraduateStudent(studentId, name, className, chinese, math, english);
                }

                manager.updateStudent(studentId, updatedStudent);
                appendText("成功修改学生: " + name + " (" + studentId + ")\n");
                dialog.dispose();
            } catch (NumberFormatException ex) {
                JOptionPane.showMessageDialog(dialog, "成绩必须为数字！", "输入错误", JOptionPane.ERROR_MESSAGE);
            }
        });

        cancelButton.addActionListener(e -> dialog.dispose());

        dialog.setVisible(true);
    }

    // 删除学生对话框
    private void deleteStudentDialog() {
        String studentId = JOptionPane.showInputDialog(this, "请输入要删除的学生学号:");
        if (studentId == null || studentId.trim().isEmpty()) return;

        Student student = manager.getStudentById(studentId);
        if (student == null) {
            JOptionPane.showMessageDialog(this, "未找到该学生！", "查找结果", JOptionPane.INFORMATION_MESSAGE);
            return;
        }

        int confirm = JOptionPane.showConfirmDialog(
                this,
                "确定要删除学生 " + student.getName() + " (" + studentId + ") 吗？",
                "确认删除",
                JOptionPane.YES_NO_OPTION
        );

        if (confirm == JOptionPane.YES_OPTION) {
            manager.deleteStudent(studentId);
            appendText("成功删除学生: " + student.getName() + " (" + studentId + ")\n");
        }
    }

    // 查看所有学生
    private void viewAllStudents() {
        List<Student> students = manager.getAllStudents();
        StringBuilder sb = new StringBuilder("所有学生信息:\n");
        sb.append("====================================================================\n");
        sb.append("学号\t姓名\t班级\t\t类型\t语文\t数学\t英语\t总分\n");
        sb.append("--------------------------------------------------------------------\n");
        for (Student student : students) {
            sb.append(student.getStudentId()).append("\t");
            sb.append(student.getName()).append("\t");
            sb.append(student.getClassName()).append("\t");
            sb.append(student.getType()).append("\t");
            sb.append(student.getChinese()).append("\t");
            sb.append(student.getMath()).append("\t");
            sb.append(student.getEnglish()).append("\t");
            sb.append(student.getTotalScore()).append("\n");
        }
        sb.append("====================================================================\n");
        appendText(sb.toString());
    }

    // 按班级查询
    private void searchByClassDialog() {
        String className = JOptionPane.showInputDialog(this, "请输入要查询的班级:");
        if (className == null || className.trim().isEmpty()) return;

        List<Student> students = manager.getStudentsByClass(className);
        if (students.isEmpty()) {
            appendText("未找到班级为 " + className + " 的学生！\n");
            return;
        }

        StringBuilder sb = new StringBuilder("班级 " + className + " 的学生信息:\n");
        sb.append("====================================================================\n");
        sb.append("学号\t姓名\t班级\t\t类型\t语文\t数学\t英语\t总分\n");
        sb.append("--------------------------------------------------------------------\n");

        for (Student student : students) {
            sb.append(student.getStudentId()).append("\t");
            sb.append(student.getName()).append("\t");
            sb.append(student.getClassName()).append("\t");
            sb.append(student instanceof UndergraduateStudent ? "本科生" : "研究生").append("\t");
            sb.append(student.getChinese()).append("\t");
            sb.append(student.getMath()).append("\t");
            sb.append(student.getEnglish()).append("\t");
            sb.append(student.getTotalScore()).append("\n");
        }

        sb.append("====================================================================\n");
        appendText(sb.toString());
    }

    // 按姓名查询
    private void searchByNameDialog() {
        String name = JOptionPane.showInputDialog(this, "请输入要查询的学生姓名:");
        if (name == null || name.trim().isEmpty()) return;

        List<Student> students = manager.getStudentsByName(name);
        if (students.isEmpty()) {
            appendText("未找到姓名为 " + name + " 的学生！\n");
            return;
        }

        StringBuilder sb = new StringBuilder("姓名为 " + name + " 的学生信息:\n");
        sb.append("====================================================================\n");
        sb.append("学号\t姓名\t班级\t\t类型\t语文\t数学\t英语\t总分\n");
        sb.append("--------------------------------------------------------------------\n");

        for (Student student : students) {
            sb.append(student.getStudentId()).append("\t");
            sb.append(student.getName()).append("\t");
            sb.append(student.getClassName()).append("\t");
            sb.append(student instanceof UndergraduateStudent ? "本科生" : "研究生").append("\t");
            sb.append(student.getChinese()).append("\t");
            sb.append(student.getMath()).append("\t");
            sb.append(student.getEnglish()).append("\t");
            sb.append(student.getTotalScore()).append("\n");
        }

        sb.append("====================================================================\n");
        appendText(sb.toString());
    }

    // 按学号查询
    private void searchByIdDialog() {
        String studentId = JOptionPane.showInputDialog(this, "请输入要查询的学生学号:");
        if (studentId == null || studentId.trim().isEmpty()) return;

        Student student = manager.getStudentById(studentId);
        if (student == null) {
            appendText("未找到学号为 " + studentId + " 的学生！\n");
            return;
        }

        StringBuilder sb = new StringBuilder("学号为 " + studentId + " 的学生信息:\n");
        sb.append("====================================================================\n");
        sb.append("学号\t姓名\t班级\t\t类型\t语文\t数学\t英语\t总分\n");
        sb.append("--------------------------------------------------------------------\n");
        sb.append(student.getStudentId()).append("\t");
        sb.append(student.getName()).append("\t");
        sb.append(student.getClassName()).append("\t");
        sb.append(student instanceof UndergraduateStudent ? "本科生" : "研究生").append("\t");
        sb.append(student.getChinese()).append("\t");
        sb.append(student.getMath()).append("\t");
        sb.append(student.getEnglish()).append("\t");
        sb.append(student.getTotalScore()).append("\n");
        sb.append("====================================================================\n");
        appendText(sb.toString());
    }

    // 按科目排序
    private void sortBySubject(String subject) {
        List<Student> sortedStudents = manager.sortBySubject(subject);
        displayStudents(sortedStudents, "按" + getSubjectName(subject) + "成绩排序：");
    }

    // 按总分排序
    private void sortByTotalScore() {
        List<Student> sortedStudents = manager.sortByTotalScore();
        displayStudents(sortedStudents, "按总分排序：");
    }

    // 按学号排序
    private void sortById() {
        List<Student> sortedStudents = manager.sortById();
        displayStudents(sortedStudents, "按学号排序：");
    }

    // 辅助方法：显示学生列表
    private void displayStudents(List<Student> students, String title) {
        StringBuilder sb = new StringBuilder(title + "\n");
        sb.append("====================================================================\n");
        sb.append("学号\t姓名\t班级\t\t类型\t语文\t数学\t英语\t总分\n");
        sb.append("--------------------------------------------------------------------\n");

        for (Student student : students) {
            sb.append(String.format("%-8s %-8s %-8s %-8s %-8.1f %-8.1f %-8.1f %-8.1f\n",
                    student.getStudentId(),
                    student.getName(),
                    student.getClassName(),
                    student.getType(),
                    student.getChinese(),
                    student.getMath(),
                    student.getEnglish(),
                    student.getTotalScore()
            ));
        }

        sb.append("====================================================================\n");
        appendText(sb.toString());
    }

    // 辅助方法：获取科目中文名
    private String getSubjectName(String subject) {
        return switch (subject.toLowerCase()) {
            case "chinese" -> "语文";
            case "math" -> "数学";
            case "english" -> "英语";
            default -> subject;
        };
    }

    // 查看本科生人数
    private void viewUndergraduateCount() {
        int count = manager.getUndergraduateCount();
        appendText("本科生人数: " + count + "\n");
    }

    // 查看研究生人数
    private void viewGraduateCount() {
        int count = manager.getGraduateCount();
        appendText("研究生人数: " + count + "\n");
    }

    // 查看总人数
    private void viewTotalCount() {
        int count = manager.getTotalCount();
        appendText("学生总人数: " + count + "\n");
    }

    // 显示关于对话框
    private void showAboutDialog() {
        JDialog dialog = new JDialog(this, "关于系统", true);
        dialog.setSize(400, 300);
        dialog.setLocationRelativeTo(this);
        dialog.setLayout(new BorderLayout());

        JPanel panel = new JPanel();
        panel.setLayout(new BoxLayout(panel, BoxLayout.Y_AXIS));
        panel.setBorder(BorderFactory.createEmptyBorder(20, 20, 20, 20));

        JLabel titleLabel = new JLabel("学生成绩管理系统");
        titleLabel.setFont(new Font("宋体", Font.BOLD, 16));
        titleLabel.setAlignmentX(Component.CENTER_ALIGNMENT);

        panel.add(Box.createVerticalStrut(10));
        panel.add(titleLabel);
        panel.add(Box.createVerticalStrut(20));

        panel.add(new JLabel("版本: v3.0"));
        panel.add(Box.createVerticalStrut(10));
        panel.add(new JLabel("完成时间: 2025-05-31"));
        panel.add(Box.createVerticalStrut(10));
        panel.add(new JLabel("作者: 夏遂冬"));
        panel.add(Box.createVerticalStrut(10));
        panel.add(new JLabel("学号: 8002124117"));
        panel.add(Box.createVerticalStrut(10));
        panel.add(new JLabel("班级: 软工2404班"));

        JButton okButton = new JButton("确定");
        okButton.addActionListener(e -> dialog.dispose());
        okButton.setAlignmentX(Component.CENTER_ALIGNMENT);

        panel.add(Box.createVerticalStrut(20));
        panel.add(okButton);

        dialog.add(panel, BorderLayout.CENTER);
        dialog.setVisible(true);
    }

    // 向输出区域添加文本
    private void appendText(String text) {
        outputArea.append(text);
        // 滚动到底部
        outputArea.setCaretPosition(outputArea.getDocument().getLength());
    }
}