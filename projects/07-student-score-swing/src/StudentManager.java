import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 学生管理类，实现学生信息的增删改查等功能
 */
public class StudentManager {
    private List<Student> students;  // 学生列表
    private FileHandler fileHandler; // 文件处理器

    public StudentManager() {
        students = new ArrayList<>();
        fileHandler = new FileHandler();
        loadStudents(); // 从文件加载学生数据
    }

    // 从文件加载学生数据
    public void loadStudents() {
        List<Student> loadedStudents = fileHandler.loadStudents();
        if (loadedStudents != null) {
            students = loadedStudents;
        }
    }

    // 添加学生
    public boolean addStudent(Student student) {
        // 检查学号是否已存在
        if (getStudentById(student.getStudentId()) != null) {
            System.err.println("添加失败: 学号 " + student.getStudentId() + " 已存在");
            return false;
        }

        students.add(student);
        return saveStudents();
    }

    // 根据学号查询学生
    public Student getStudentById(String studentId) {
        return students.stream()
                .filter(s -> s.getStudentId().equals(studentId))
                .findFirst()
                .orElse(null);
    }

    // 保存学生数据到文件
    private boolean saveStudents() {
        return fileHandler.saveStudents(students);
    }

    // 修改学生信息
    public boolean updateStudent(String studentId, Student updatedStudent) {
        for (int i = 0; i < students.size(); i++) {
            if (students.get(i).getStudentId().equals(studentId)) {
                students.set(i, updatedStudent);
                return saveStudents();
            }
        }

        System.err.println("修改失败: 未找到学号为 " + studentId + " 的学生");
        return false;
    }

    // 删除学生
    public boolean deleteStudent(String studentId) {
        boolean result = students.removeIf(s -> s.getStudentId().equals(studentId));

        if (result) {
            return saveStudents();
        } else {
            System.err.println("删除失败: 未找到学号为 " + studentId + " 的学生");
            return false;
        }
    }

    // 获取所有学生
    public List<Student> getAllStudents() {
        return new ArrayList<>(students);
    }

    // 根据班级查询学生
    public List<Student> getStudentsByClass(String className) {
        return students.stream()
                .filter(s -> s.getClassName().equals(className))
                .collect(Collectors.toList());
    }

    // 根据姓名查询学生
    public List<Student> getStudentsByName(String name) {
        return students.stream()
                .filter(s -> s.getName().equals(name))
                .collect(Collectors.toList());
    }

    // 按科目排序（返回新列表）
    public List<Student> sortBySubject(String subject) {
        List<Student> sortedStudents = new ArrayList<>(students);
        Comparator<Student> comparator;

        switch (subject.toLowerCase()) {
            case "chinese":
                comparator = Comparator.comparingDouble(Student::getChinese).reversed();
                break;
            case "math":
                comparator = Comparator.comparingDouble(Student::getMath).reversed();
                break;
            case "english":
                comparator = Comparator.comparingDouble(Student::getEnglish).reversed();
                break;
            default:
                throw new IllegalArgumentException("Invalid subject: " + subject);
        }

        sortedStudents.sort(comparator);
        return sortedStudents;
    }

    // 按总分排序（返回新列表）
    public List<Student> sortByTotalScore() {
        return students.stream()
                .sorted(Comparator.comparingDouble(Student::getTotalScore).reversed())
                .collect(Collectors.toList());
    }

    // 按学号排序（返回新列表）
    public List<Student> sortById() {
        return students.stream()
                .sorted(Comparator.comparing(Student::getStudentId))
                .collect(Collectors.toList());
    }

    // 获取本科生人数
    public int getUndergraduateCount() {
        return (int) students.stream()
                .filter(s -> s instanceof UndergraduateStudent)
                .count();
    }

    // 获取研究生人数
    public int getGraduateCount() {
        return (int) students.stream()
                .filter(s -> s instanceof GraduateStudent)
                .count();
    }

    // 获取总人数
    public int getTotalCount() {
        return students.size();
    }
}