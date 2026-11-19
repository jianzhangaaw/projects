import java.io.Serializable;

/**
 * 学生抽象类，定义学生基本属性和方法
 */
public abstract class Student implements Serializable {
    private static final long serialVersionUID = 1L; // 添加序列化版本号
    protected String studentId;  // 学号
    protected String name;       // 姓名
    protected String className;  // 班级
    protected double chinese;    // 语文成绩
    protected double math;       // 数学成绩
    protected double english;    // 英语成绩

    // 构造函数
    public Student(String studentId, String name, String className,
                   double chinese, double math, double english) {
        this.studentId = studentId;
        this.name = name;
        this.className = className;
        this.chinese = chinese;
        this.math = math;
        this.english = english;
    }

    // 获取学生类型（抽象方法，由子类实现）
    public abstract String getType();

    // 计算总成绩
    public double getTotalScore() {
        return chinese + math + english;
    }

    // Getters and Setters
    public String getStudentId() {
        return studentId;
    }

    public void setStudentId(String studentId) {
        this.studentId = studentId;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getClassName() {
        return className;
    }

    public void setClassName(String className) {
        this.className = className;
    }

    public double getChinese() {
        return chinese;
    }

    public void setChinese(double chinese) {
        this.chinese = chinese;
    }

    public double getMath() {
        return math;
    }

    public void setMath(double math) {
        this.math = math;
    }

    public double getEnglish() {
        return english;
    }

    public void setEnglish(double english) {
        this.english = english;
    }

    @Override
    public String toString() {
        return String.format(
                "学号: %s, 姓名: %s, 班级: %s, 类型: %s, 语文: %.1f, 数学: %.1f, 英语: %.1f, 总分: %.1f",
                studentId, name, className, getType(), chinese, math, english, getTotalScore());
    }
}    